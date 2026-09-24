package fixtures

// Fixture: known-vulnerable Go crypto usage
// This file is intentionally insecure — for test purposes ONLY

import (
	"crypto/rsa"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/md5"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/tls"
	"golang.org/x/crypto/ed25519"
)

// RSA key generation — CRITICAL
func GenerateRSAKey() {
	rsa.GenerateKey(nil, 2048)
}

// ECDSA with P-256 — CRITICAL
func GenerateECDSAKey() {
	ecdsa.GenerateKey(elliptic.P256(), nil)
}

// Ed25519 — CRITICAL
func GenerateEd25519Key() {
	ed25519.GenerateKey(nil)
}

// MD5 — MEDIUM
func LegacyHash(data []byte) []byte {
	h := md5.New()
	h.Write(data)
	return h.Sum(nil)
}

// SHA-1 — MEDIUM
func OldHash(data []byte) []byte {
	h := sha1.New()
	h.Write(data)
	return h.Sum(nil)
}

// SHA-256 — SAFE
func GoodHash(data []byte) []byte {
	h := sha256.New()
	h.Write(data)
	return h.Sum(nil)
}

// TLS config — HIGH (harvest risk)
func NewTLSConfig() *tls.Config {
	return &tls.Config{
		MinVersion: tls.VersionTLS12,
	}
}
