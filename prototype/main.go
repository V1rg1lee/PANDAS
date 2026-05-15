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
}

type StaticPeer struct {
	Nick string
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

	log.Printf("Running GossipSub node nick=%s ip=%s tcp=%d peer=%s topic=%s", config.Nick, config.IP, config.ListenPort, h.ID(), config.Topic)

	pub, err := CreatePubSubWithTopic(h, ctx, config.LogDirectory, config.Nick, config.Topic, config.MessageBytes)
	if err != nil {
		log.Fatalf("failed to create GossipSub: %v", err)
	}
	go pub.ReadLoop()

	peers, err := readStaticPeers(config.NodeFile, h.ID())
	if err != nil {
		log.Fatalf("failed to read topology: %v", err)
	}
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

func readStaticPeers(path string, ownID peer.ID) ([]StaticPeer, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	records, err := csv.NewReader(file).ReadAll()
	if err != nil {
		return nil, err
	}

	peers := make([]StaticPeer, 0, len(records))
	for row, record := range records {
		if len(record) != 6 {
			return nil, fmt.Errorf("invalid topology row %d: expected 6 columns, got %d", row+1, len(record))
		}

		addr, err := multiaddr.NewMultiaddr(record[4])
		if err != nil {
			return nil, fmt.Errorf("invalid multiaddr at row %d: %w", row+1, err)
		}

		info, err := peer.AddrInfoFromP2pAddr(addr)
		if err != nil {
			return nil, fmt.Errorf("invalid peer info at row %d: %w", row+1, err)
		}
		if info.ID == ownID {
			continue
		}

		peers = append(peers, StaticPeer{
			Nick: record[0],
			Info: info,
		})
	}

	return peers, nil
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
			log.Printf("Connected static peer nick=%s peer=%s", staticPeer.Nick, id)
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
		if err := pub.Publish(publishID); err != nil {
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
			log.Printf("GossipSub message received sender=%s sequence=%d bytes=%d", msg.SenderID, msg.Sequence, len(msg.Payload))
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

func tracePath(logDir string, nick string) string {
	return filepath.Join(logDir, nick+".trace")
}
