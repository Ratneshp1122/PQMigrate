package semanticfixtures

import (
	"crypto/rand"
	crsa "crypto/rsa"
)

func sign(digest []byte) ([]byte, error) {
	key, err := crsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}
	return crsa.SignPSS(rand.Reader, key, 0, digest, nil)
}
