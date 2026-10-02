package semanticfixtures

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
)

func wrap() ([]byte, error) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}
	sessionKey := make([]byte, 32)
	if _, err = rand.Read(sessionKey); err != nil {
		return nil, err
	}
	return rsa.EncryptOAEP(sha256.New(), rand.Reader, &key.PublicKey, sessionKey, nil)
}
