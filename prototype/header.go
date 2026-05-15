package main

import (
	"context"
	"encoding/json"
	"log"

	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/libp2p/go-libp2p/core/host"
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
}

func CreatePubSubWithTopic(h host.Host, ctx context.Context, logDirectory string, nick string, topicName string, messageSize int) (*GossipPubSub, error) {
	tracer, err := pubsub.NewJSONTracer(tracePath(logDirectory, nick))
	if err != nil {
		return nil, err
	}

	ps, err := pubsub.NewGossipSub(ctx, h, pubsub.WithEventTracer(tracer))
	if err != nil {
		return nil, err
	}

	topic, err := ps.Join(topicName)
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
		messageSize: messageSize,
	}, nil
}

func (p *GossipPubSub) Publish(sequence int) error {
	message := &GossipMessage{
		SenderID: p.host.ID().String(),
		Sequence: sequence,
		Payload:  make([]byte, p.messageSize),
	}

	msgBytes, err := json.Marshal(message)
	if err != nil {
		return err
	}

	log.Printf("GossipSub publish sequence=%d bytes=%d", sequence, len(message.Payload))
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
