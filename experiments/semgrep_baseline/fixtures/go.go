package fixture
import (
    rsa "crypto/rsa"
    "math/big"
)
func sample(k *rsa.PrivateKey, n *big.Int) {
    // ruleid: pqmigrate.go.crypto-rsa-key_generate,pqmigrate.go.candidate-generatekey
    rsa.GenerateKey(random, 2048)
    // ruleid: pqmigrate.go.crypto-rsa-sign
    rsa.SignPKCS1v15(random, k, hash, message)
    // ruleid: pqmigrate.go.candidate-sign
    n.Sign() // Syntax candidate deliberately remains uncertain.
}
// ok: pqmigrate.go.candidate-sign
func Sign() {}
