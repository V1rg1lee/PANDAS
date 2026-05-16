package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/libp2p/go-libp2p/core/host"
	"github.com/libp2p/go-libp2p/core/peer"
)

const gossipBufferSize = 128

type GossipPubSub struct {
	host        host.Host
	ctx         context.Context
	topic       *pubsub.Topic
	sub         *pubsub.Subscription
	Messages    chan *GossipMessage
	messageSize int
}

type GossipMessage struct {
	SenderID string `json:"sender_id"`
	Sequence int    `json:"sequence"`
	Payload  []byte `json:"payload"`
	Invalid  bool   `json:"invalid,omitempty"`
}

type PubSubConfig struct {
	LogDirectory                  string
	Nick                          string
	Topic                         string
	MessageBytes                  int
	EnablePeerScore               bool
	PeerRoles                     map[peer.ID]string
	AppSpecificDegradedScore      float64
	ScoreInspectInterval          time.Duration
	GossipD                       int
	GossipDlo                     int
	GossipDhi                     int
	GossipDscore                  int
	GossipDout                    int
	InvalidMessagePenaltyWeight   float64
	InvalidMessagePenaltyHalfLife time.Duration
}

func CreatePubSubWithTopic(h host.Host, ctx context.Context, config PubSubConfig) (*GossipPubSub, error) {
	tracer, err := pubsub.NewJSONTracer(tracePath(config.LogDirectory, config.Nick))
	if err != nil {
		return nil, err
	}

	options, err := gossipSubOptions(config, tracer)
	if err != nil {
		return nil, err
	}

	ps, err := pubsub.NewGossipSub(ctx, h, options...)
	if err != nil {
		return nil, err
	}

	if err := ps.RegisterTopicValidator(config.Topic, func(ctx context.Context, from peer.ID, msg *pubsub.Message) bool {
		return validateGossipMessage(h.ID(), from, msg)
	}); err != nil {
		return nil, err
	}

	topic, err := ps.Join(config.Topic)
	if err != nil {
		return nil, err
	}

	sub, err := topic.Subscribe()
	if err != nil {
		return nil, err
	}

	return &GossipPubSub{
		host:        h,
		ctx:         ctx,
		topic:       topic,
		sub:         sub,
		Messages:    make(chan *GossipMessage, gossipBufferSize),
		messageSize: config.MessageBytes,
	}, nil
}

func gossipSubOptions(config PubSubConfig, tracer *pubsub.JSONTracer) ([]pubsub.Option, error) {
	params := pubsub.DefaultGossipSubParams()
	if config.GossipD > 0 {
		params.D = config.GossipD
	}
	if config.GossipDlo > 0 {
		params.Dlo = config.GossipDlo
	}
	if config.GossipDhi > 0 {
		params.Dhi = config.GossipDhi
	}
	if config.GossipDscore > 0 {
		params.Dscore = config.GossipDscore
	}
	if config.GossipDout > 0 {
		params.Dout = config.GossipDout
	}

	options := []pubsub.Option{
		pubsub.WithEventTracer(tracer),
		pubsub.WithGossipSubParams(params),
	}

	if !config.EnablePeerScore {
		return options, nil
	}

	invalidDecay := pubsub.ScoreParameterDecay(config.InvalidMessagePenaltyHalfLife)
	scoreParams := &pubsub.PeerScoreParams{
		SkipAtomicValidation: true,
		AppSpecificScore: func(p peer.ID) float64 {
			if config.PeerRoles[p] == degradedRole {
				return config.AppSpecificDegradedScore
			}
			return 0
		},
		AppSpecificWeight: 1,
		Topics: map[string]*pubsub.TopicScoreParams{
			config.Topic: {
				SkipAtomicValidation:           true,
				TopicWeight:                    1,
				TimeInMeshWeight:               0.01,
				TimeInMeshQuantum:              time.Second,
				TimeInMeshCap:                  10,
				FirstMessageDeliveriesWeight:   0.2,
				FirstMessageDeliveriesDecay:    pubsub.ScoreParameterDecay(time.Minute),
				FirstMessageDeliveriesCap:      20,
				InvalidMessageDeliveriesWeight: config.InvalidMessagePenaltyWeight,
				InvalidMessageDeliveriesDecay:  invalidDecay,
			},
		},
		DecayInterval: time.Second,
		DecayToZero:   0.01,
		RetainScore:   time.Hour,
	}
	thresholds := &pubsub.PeerScoreThresholds{
		SkipAtomicValidation:        true,
		GossipThreshold:             -10,
		PublishThreshold:            -20,
		GraylistThreshold:           -100,
		OpportunisticGraftThreshold: 5,
	}

	options = append(options, pubsub.WithPeerScore(scoreParams, thresholds))
	if config.ScoreInspectInterval > 0 {
		inspect, err := newScoreInspector(config.LogDirectory, config.Nick)
		if err != nil {
			return nil, err
		}
		options = append(options, pubsub.WithPeerScoreInspect(inspect, config.ScoreInspectInterval))
	}

	return options, nil
}

func validateGossipMessage(ownID peer.ID, from peer.ID, msg *pubsub.Message) bool {
	decoded := new(GossipMessage)
	if err := json.Unmarshal(msg.Data, decoded); err != nil {
		log.Printf("GossipSub validator rejected malformed message from=%s: %v", from, err)
		return false
	}
	if from == ownID {
		return true
	}
	if decoded.Invalid {
		log.Printf("GossipSub validator rejected invalid message from=%s sequence=%d", from, decoded.Sequence)
		return false
	}
	return true
}

func newScoreInspector(logDirectory string, nick string) (pubsub.PeerScoreInspectFn, error) {
	if err := os.MkdirAll(logDirectory, 0o755); err != nil {
		return nil, err
	}

	path := filepath.Join(logDirectory, nick+".scores.csv")
	file, err := os.Create(path)
	if err != nil {
		return nil, err
	}

	writer := csv.NewWriter(file)
	if err := writer.Write([]string{"timestamp", "local_node", "peer_id", "score"}); err != nil {
		_ = file.Close()
		return nil, err
	}
	writer.Flush()

	var mu sync.Mutex
	inspect := func(scores map[peer.ID]float64) {
		mu.Lock()
		defer mu.Unlock()

		now := time.Now().Format(time.RFC3339Nano)
		for peerID, score := range scores {
			if err := writer.Write([]string{now, nick, peerID.String(), floatString(score)}); err != nil {
				log.Printf("failed to write peer score snapshot: %v", err)
				return
			}
		}
		writer.Flush()
	}

	return inspect, nil
}

func floatString(value float64) string {
	return strconv.FormatFloat(value, 'f', 6, 64)
}

func (p *GossipPubSub) Publish(sequence int, invalid bool) error {
	message := &GossipMessage{
		SenderID: p.host.ID().String(),
		Sequence: sequence,
		Payload:  make([]byte, p.messageSize),
		Invalid:  invalid,
	}

	msgBytes, err := json.Marshal(message)
	if err != nil {
		return err
	}

	log.Printf("GossipSub publish sequence=%d bytes=%d invalid=%t", sequence, len(message.Payload), invalid)
	return p.topic.Publish(p.ctx, msgBytes)
}

func (p *GossipPubSub) ReadLoop() {
	defer close(p.Messages)

	for {
		msg, err := p.sub.Next(p.ctx)
		if err != nil {
			return
		}
		if msg.ReceivedFrom == p.host.ID() {
			continue
		}

		decoded := new(GossipMessage)
		if err := json.Unmarshal(msg.Data, decoded); err != nil {
			log.Printf("failed to decode GossipSub message: %v", err)
			continue
		}

		p.Messages <- decoded
	}
}
