# Protocol specification for `unchanging.ink`

## Request timestamp

### Request

````http request
POST /api/v1/st/ HTTP/1.1
Content-Type: application/json

{
    "data": "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
    "options": []
}
````

`data` MUST be valid UTF-8 and MUST NOT exceed 256 bytes in length. It is recommended that `data` be constructed as a hash function identifier followed by the canonical text representation for that hash.

`options` is an array of options (optional, assumed to be empty when missing):

* `wait`: Wait for issuance of inclusion proof, return inclusion proof with response

### Signed statement

````json
{
    "data": "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
    "kid": "xxx",
    "timestamp": "2021-04-05T23:39:42.944682Z",
    "typ": "st",
    "version": "1"
}
````

Server computes signature of the canonical representation (keys sorted alphabetically, optional whitespace removed, UTF-8 normalized, JSON encoding normalized) of the signed statement.

### Response

````http response
HTTP/1.1 200 OK
Content-Type: application/json

{
    "version": "1",
    "kid": "xxx",
    "timestamp": "2021-04-05T23:39:42.944682Z",
    "id": "154084e6-9573-41a1-9ab4-f2724dae23b3",
    "typ": "st",
    "signature": "...base64-encoded..."
}
````

## Compute Merkle inclusion proof
Set *interval* to a small time value on the order of 1s - 5s.

Inner Merkle tree: List of all `signature` issued within *interval*, ordered by `timestamp`, then `signature`. Construct binary Merkle Tree (as per RFC 6962 section 2.1) for this list. Designate root as *interval tree hash* (`ith`).

## Get Merkle inclusion proof

### Request

````http request
GET /api/v1/st/154084e6-9573-41a1-9ab4-f2724dae23b3/ HTTP/1.1

````

### Response

````http response
HTTP/1.1 200 OK
Content-Type: application/json

{
    "version": "1",
    "kid": "xxx",
    "timestamp": "2021-04-05T23:39:42.944682Z",
    "id": "154084e6-9573-41a1-9ab4-f2724dae23b3",
    "typ": "st",
    "signature": "...base64-encoded...",
    "proof": {
    	"ith": "...base64-encoded...",
    	"a": 123,
    	"path": ["...base64-encoded...", "...base64-encoded...", "...base64-encoded...", "...base64-encoded..."]
    }
}
````

`proof` is encoded as follows: `ith` is the interval tree hash, `a` and `path` are as defined based on RFC 6962 section 2.1.1. Specifically, `path`is `PATH(m, {interval tree})` and `a` is `m >> (ceil(log2(n)) - len(path))`. That is, `a` is defined as the `len(path)` highest order bits of `m`, if `m` is represented as an integer of the minimal length that fits `n`. This is another way to say that `a` is the node address of `m` in the interval tree, where, starting from the highest order bits, `0`is the left (lower indexes) subtree and `1`is the right (higher indexes) subtree.

### Verify proof

This convention allows the proof verification to be implemented as follows:

````python
def verify(signature: bytes, ith: bytes, a: int, path: List[bytes]) -> bool:
    current = hashfunc(b'\x00' + signature)
    for node in path:
        if a & 1:  # Walking the tree upwards, thus start with the end of the address
            # `current` represents right side, therefore add node to left side
            current = hashfunc(b'\x01' + node + current)
        else:
            # `current` represents left side, add node to right side
            current = hashfunc(b'\x01' + current + node)
        a >>= 1  # Lowest bit of `a` has been handled, strip it off
    return current == ith  # `current` should now be the interval tree hash
````

hashfunc is SHA-512 for version 1.