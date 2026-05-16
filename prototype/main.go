package main

import (
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p/core/crypto"
	"github.com/libp2p/go-libp2p/core/host"
	"github.com/libp2p/go-libp2p/core/peer"
	"github.com/multiformats/go-multiaddr"
)

const (
	honestRole   = "node"
	degradedRole = "degraded"
)

type Config struct {
	IP                 string
	ListenPort         int
	Nick               string
	Key                string
	LogDirectory       string
	NodeFile           string
	ExperimentDuration int
	Debug              bool
	Topic              string
	PublishInterval    int
	MessageBytes       int
	ConnectTimeout     int
	Role               string
	EnablePeerScore    bool
	GossipD            int
	GossipDlo          int
	GossipDhi          int
	GossipDscore       int
	GossipDout         int
	ScoreInspect       int
	AppDegradedScore   float64
	InvalidPenalty     float64
	InvalidPenaltyTTL  int
	InvalidPublishPct  int
	DegradedDropPct    int
}

type StaticPeer struct {
	Nick string
	Role string
	Info *peer.AddrInfo
}

func main() {
	config := parseFlags()

	if err := os.MkdirAll(config.LogDirectory, 0o755); err != nil {
		log.Fatalf("failed to create log directory %s: %v", config.LogDirectory, err)
	}

	log.SetPrefix(config.Nick + ": ")
	log.SetFlags(log.Lmicroseconds)
	if !config.Debug {
		log.SetOutput(os.Stdout)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	h, err := makeHost(config)
	if err != nil {
		log.Fatalf("failed to create libp2p host: %v", err)
	}
	defer h.Close()

	peers, peerRoles, ownRole, err := readStaticTopology(config.NodeFile, h.ID())
	if err != nil {
		log.Fatalf("failed to read topology: %v", err)
	}
	if config.Role == "" {
		config.Role = ownRole
	}
	if config.Role == "" {
		config.Role = honestRole
	}

	log.Printf(
		"Running GossipSub node nick=%s role=%s ip=%s tcp=%d peer=%s topic=%s scoring=%t invalid_publish_pct=%d degraded_drop_pct=%d",
		config.Nick,
		config.Role,
		config.IP,
		config.ListenPort,
		h.ID(),
		config.Topic,
		config.EnablePeerScore,
		config.InvalidPublishPct,
		config.DegradedDropPct,
	)

	pub, err := CreatePubSubWithTopic(h, ctx, PubSubConfig{
		LogDirectory:                  config.LogDirectory,
		Nick:                          config.Nick,
		Topic:                         config.Topic,
		MessageBytes:                  config.MessageBytes,
		EnablePeerScore:               config.EnablePeerScore,
		PeerRoles:                     peerRoles,
		AppSpecificDegradedScore:      config.AppDegradedScore,
		ScoreInspectInterval:          time.Duration(config.ScoreInspect) * time.Second,
		GossipD:                       config.GossipD,
		GossipDlo:                     config.GossipDlo,
		GossipDhi:                     config.GossipDhi,
		GossipDscore:                  config.GossipDscore,
		GossipDout:                    config.GossipDout,
		InvalidMessagePenaltyWeight:   config.InvalidPenalty,
		InvalidMessagePenaltyHalfLife: time.Duration(config.InvalidPenaltyTTL) * time.Second,
	})
	if err != nil {
		log.Fatalf("failed to create GossipSub: %v", err)
	}
	go pub.ReadLoop()

	connectStaticPeers(ctx, h, peers, time.Duration(config.ConnectTimeout)*time.Second)

	if err := runGossip(ctx, pub, config); err != nil {
		log.Fatalf("GossipSub run failed: %v", err)
	}

	log.Printf("GossipSub node done")
}

func parseFlags() Config {
	config := Config{}

	flag.StringVar(&config.IP, "ip", "127.0.0.1", "IP to bind to")
	flag.IntVar(&config.ListenPort, "port", 9000, "TCP port to listen on")
	flag.StringVar(&config.Nick, "nick", "", "node nickname")
	flag.StringVar(&config.Key, "key", "", "private key file")
	flag.StringVar(&config.LogDirectory, "log", "./log/", "directory for GossipSub trace files")
	flag.StringVar(&config.NodeFile, "node", "./nodes.csv", "CSV topology file")
	flag.IntVar(&config.ExperimentDuration, "duration", 80, "experiment duration in seconds")
	flag.BoolVar(&config.Debug, "debug", false, "print debug logs")
	flag.StringVar(&config.Topic, "gossipTopic", "gossipsub-smoke", "GossipSub topic")
	flag.IntVar(&config.PublishInterval, "gossipInterval", 5, "seconds between publishes")
	flag.IntVar(&config.MessageBytes, "gossipMessageBytes", 512, "GossipSub payload size in bytes")
	flag.IntVar(&config.ConnectTimeout, "connTimeout", 30, "static peer connection retry window in seconds")
	flag.StringVar(&config.Role, "role", "", "local node role; defaults to the role column in nodes.csv")
	flag.BoolVar(&config.EnablePeerScore, "enablePeerScore", false, "enable GossipSub peer scoring")
	flag.IntVar(&config.GossipD, "gossipD", 0, "GossipSub target mesh degree; 0 keeps libp2p default")
	flag.IntVar(&config.GossipDlo, "gossipDlo", 0, "GossipSub low mesh degree; 0 keeps libp2p default")
	flag.IntVar(&config.GossipDhi, "gossipDhi", 0, "GossipSub high mesh degree; 0 keeps libp2p default")
	flag.IntVar(&config.GossipDscore, "gossipDscore", 0, "GossipSub scored peers retained during prune; 0 keeps libp2p default")
	flag.IntVar(&config.GossipDout, "gossipDout", 0, "GossipSub outbound mesh quota; 0 keeps libp2p default")
	flag.IntVar(&config.ScoreInspect, "scoreInspect", 0, "seconds between peer score CSV snapshots; 0 disables score output")
	flag.Float64Var(&config.AppDegradedScore, "appDegradedScore", -50, "application-specific score assigned to peers marked degraded")
	flag.Float64Var(&config.InvalidPenalty, "invalidPenalty", -20, "topic score weight for invalid message deliveries")
	flag.IntVar(&config.InvalidPenaltyTTL, "invalidPenaltyTTL", 60, "invalid message delivery penalty half-life in seconds")
	flag.IntVar(&config.InvalidPublishPct, "degradedInvalidPublishPct", 0, "percentage of degraded node publishes marked invalid")
	flag.IntVar(&config.DegradedDropPct, "degradedDropPct", 0, "percentage of received app messages ignored by degraded nodes")
	flag.Parse()

	if config.Nick == "" {
		config.Nick = fmt.Sprintf("%s-%d", config.IP, config.ListenPort)
	}
	if config.Key == "" {
		log.Fatal("missing required -key")
	}
	if config.ExperimentDuration <= 0 {
		log.Fatal("-duration must be positive")
	}
	if config.PublishInterval <= 0 {
		log.Fatal("-gossipInterval must be positive")
	}
	if config.MessageBytes < 0 {
		log.Fatal("-gossipMessageBytes must be zero or positive")
	}
	if config.ConnectTimeout <= 0 {
		log.Fatal("-connTimeout must be positive")
	}
	if config.InvalidPenaltyTTL <= 0 {
		log.Fatal("-invalidPenaltyTTL must be positive")
	}
	if !validPercent(config.InvalidPublishPct) {
		log.Fatal("-degradedInvalidPublishPct must be between 0 and 100")
	}
	if !validPercent(config.DegradedDropPct) {
		log.Fatal("-degradedDropPct must be between 0 and 100")
	}

	return config
}

func makeHost(config Config) (host.Host, error) {
	privBytes, err := os.ReadFile(config.Key)
	if err != nil {
		return nil, err
	}

	priv, err := crypto.UnmarshalPrivateKey(privBytes)
	if err != nil {
		return nil, err
	}

	listenAddr := fmt.Sprintf("/ip4/%s/tcp/%d", config.IP, config.ListenPort)
	return libp2p.New(
		libp2p.Identity(priv),
		libp2p.ListenAddrStrings(listenAddr),
		libp2p.DisableRelay(),
	)
}

func readStaticTopology(path string, ownID peer.ID) ([]StaticPeer, map[peer.ID]string, string, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, nil, "", err
	}
	defer file.Close()

	records, err := csv.NewReader(file).ReadAll()
	if err != nil {
		return nil, nil, "", err
	}

	peers := make([]StaticPeer, 0, len(records))
	roles := make(map[peer.ID]string, len(records))
	ownRole := ""
	for row, record := range records {
		if len(record) != 6 {
			return nil, nil, "", fmt.Errorf("invalid topology row %d: expected 6 columns, got %d", row+1, len(record))
		}

		addr, err := multiaddr.NewMultiaddr(record[4])
		if err != nil {
			return nil, nil, "", fmt.Errorf("invalid multiaddr at row %d: %w", row+1, err)
		}

		info, err := peer.AddrInfoFromP2pAddr(addr)
		if err != nil {
			return nil, nil, "", fmt.Errorf("invalid peer info at row %d: %w", row+1, err)
		}
		role := normalizeRole(record[5])
		roles[info.ID] = role
		if info.ID == ownID {
			ownRole = role
			continue
		}

		peers = append(peers, StaticPeer{
			Nick: record[0],
			Role: role,
			Info: info,
		})
	}

	return peers, roles, ownRole, nil
}

func connectStaticPeers(ctx context.Context, h host.Host, peers []StaticPeer, timeout time.Duration) {
	pending := make(map[peer.ID]StaticPeer, len(peers))
	for _, staticPeer := range peers {
		pending[staticPeer.Info.ID] = staticPeer
	}

	if len(pending) == 0 {
		log.Printf("No static peers to connect")
		return
	}

	deadline := time.Now().Add(timeout)
	for len(pending) > 0 && time.Now().Before(deadline) {
		for id, staticPeer := range pending {
			connectCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
			err := h.Connect(connectCtx, *staticPeer.Info)
			cancel()
			if err != nil {
				log.Printf("Static peer connect failed nick=%s peer=%s: %v", staticPeer.Nick, id, err)
				continue
			}
			log.Printf("Connected static peer nick=%s role=%s peer=%s", staticPeer.Nick, staticPeer.Role, id)
			delete(pending, id)
		}

		if len(pending) > 0 {
			time.Sleep(1 * time.Second)
		}
	}

	if len(pending) > 0 {
		log.Printf("Continuing with %d unconnected static peers", len(pending))
	}
}

func runGossip(ctx context.Context, pub *GossipPubSub, config Config) error {
	duration := time.Duration(config.ExperimentDuration) * time.Second
	interval := time.Duration(config.PublishInterval) * time.Second

	publishTicker := time.NewTicker(interval)
	defer publishTicker.Stop()

	endTimer := time.NewTimer(duration)
	defer endTimer.Stop()

	time.Sleep(2 * time.Second)
	publishID := 0

	publish := func() {
		invalid := config.Role == degradedRole && percentHit(publishID, config.InvalidPublishPct)
		if err := pub.Publish(publishID, invalid); err != nil {
			log.Printf("GossipSub publish failed message=%d: %v", publishID, err)
		}
		publishID++
	}

	publish()
	for {
		select {
		case <-endTimer.C:
			return nil
		case <-publishTicker.C:
			publish()
		case msg, ok := <-pub.Messages:
			if !ok {
				return nil
			}
			if config.Role == degradedRole && percentHit(msg.Sequence, config.DegradedDropPct) {
				log.Printf("GossipSub degraded drop sender=%s sequence=%d bytes=%d", msg.SenderID, msg.Sequence, len(msg.Payload))
				continue
			}
			log.Printf("GossipSub message received sender=%s sequence=%d bytes=%d", msg.SenderID, msg.Sequence, len(msg.Payload))
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

func normalizeRole(role string) string {
	if role == degradedRole {
		return degradedRole
	}
	return honestRole
}

func validPercent(value int) bool {
	return value >= 0 && value <= 100
}

func percentHit(sequence int, pct int) bool {
	if pct <= 0 {
		return false
	}
	if pct >= 100 {
		return true
	}
	return (sequence*37)%100 < pct
}

func tracePath(logDir string, nick string) string {
	return filepath.Join(logDir, nick+".trace")
}
