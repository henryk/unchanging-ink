# Protocol specification for `unchanging.ink`

The API can be used with messages in CBOR encoding or optionally JSON encoding, as selected by `Content-Type` and `Accept` headers. The response will be in the same format as the request, unless the `Accept` header specifies otherwise.

The native format is CBOR, and the JSON encoding is only offered as a convenience feature to web developers. The type mapping is as follows:

| CBOR                 | JSON   | Notes                                                            | field restrictions |
|----------------------|--------|------------------------------------------------------------------|--------------------|
| Integer (0, 1)       | Number |                                                                  |                    |
| Bytestring (2)       | String | Encoded in Base64                                                | hash               |
| String (3)           | String | Required to be valid UTF-8                                       |                    |
| Array (4)            | Array  |                                                                  |                    |
| Map (5)              | Object |                                                                  |                    |
| Timestamp (6, Tag 0) | String | Full ISO datetime string, with fractional seconds, in Z timezone | timestamp          |


Note: For improved readability the following documentation will show CBOR content in diagnostic notation.

## Request timestamp

### Request

````http request
POST /api/v1/ts/ HTTP/1.1
Content-Type: application/cbor

{
    "data": "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
    "options": ["wait"]
}
````

`data` MUST be valid UTF-8 and MUST NOT exceed 256 bytes in length. It is recommended that `data` be constructed as a hash function identifier followed by the canonical text representation for that hash.

`options` is an array of options (optional, assumed to be empty when missing, case-sensitive):

* `wait`: Wait for issuance of inclusion proof, return inclusion proof with response
* `tag:...`: Attach a retrieval tag to the provisional timestamp. The must not exceed 36 characters and the caller is responsible for uniqueness. Recommended: use a UUID in canonical lower-case format, example: `tag:f3109b67-3be9-405f-a7ca-a7b1f80b1e65`.

### Timestamp structure

````cbor
{
    "data": "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
    "timestamp": 0("2021-04-05T23:39:42.944682Z"),
    "typ": "ts",
    "version": "1"
}
````

The only currently defined version is `"1"` (as a string). In this version, a SHA-512 hash is calculated over the CBOR representation of this timestamp structure. This hash is designated `hash` in the following.

**NOTE:** Internal operations always use CBOR, even if input/output is JSON.

The response contains all data necessary to construct this data and is delivered with a `Location` header that specifies the REST API location of the response.

### Response

````http response
HTTP/1.1 200 OK
Content-Type: application/cbor
Location: /api/v1/ts/154084e6-9573-41a1-9ab4-f2724dae23b3/

{
    "hash": h'53C650E2F30364B9603D73016FA9....FIXME...86402B600C96765900D625F3C86425604023E8418CC1442EC902DADF6'
    "timestamp": 0("2021-04-05T23:39:42.944682Z"),
    "typ": "ts",
    "version": "1"
}
````

-----------------------------

**FIXME** The following has not been updated

-----------------------------

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
        "mth": "...url...",
    	"ith": "...base64-encoded...",
    	"a": 123,
    	"path": ["...base64-encoded...", "...base64-encoded...", "...base64-encoded...", "...base64-encoded..."]
    }
}
````

`proof` is encoded as follows: `ith` is the interval tree hash, `a` and `path` are as defined based on RFC 6962 section 2.1.1. Specifically, `path`is `PATH(m, {interval tree})` and `a` is `m >> (ceil(log2(n)) - len(path))`. That is, `a` is defined as the `len(path)` highest order bits of `m`, if `m` is represented as an integer of the minimal length that fits `n`. This is another way to say that `a` is the node address of `m` in the interval tree, where, starting from the highest order bits, `0`is the left (lower indexes) subtree and `1`is the right (higher indexes) subtree.

````
                                                  [root]
                                               (a=''_2=0x0)
                             / 0                                            1 \
                       (a=0_2=0x0)                                       (a=1_2=0x1)
              / 0                       1 \                          / 0            1 \
         (a=00_2=0x0)               (a=10_2=0x2)                (a=10_2=0x3)            \
        / 0       1 \              / 0        1 \              / 0        1 \             \
(0x000_2=0x0) (0x001_2=0x1) (0x010_2=0x2) (0x011_2=0x3) (0x100_2=0x4) (0x101_2=0x5)  (0x11_2=0x3)
    [node 0]     [node 1]      [node 2]      [node 3]      [node 4]      [node 5]      [node 6]
````

Note that `a` as an integer is not unique for all nodes, but the pair `(a, len(path))` is unique.

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

`hashfunc` is SHA-512 for version 1.

### Main Merkle tree

The `mth` member of `proof` provides a reference to the main Merkle tree in shortened URL format: `authority/i#version:mth` with the following parts:

* `authority` is a DNS name of the authority managing the tree, such as `unchanging.ink`
* `i` is the interval index as an integer encoded base 10, starting at `0`
* `version` is the version identifier, currently `v1`
* `mth` is the main tree hash at tree height `i`, base64 encoded

By convention interpreting this string as an HTTP URL should lead to a human readable web site with further information.

## Monitor log

### Request live log

````http request
GET /api/v1/mth/live HTTP/1.1
Connection: Upgrade
Upgrade: websocket

````

This opens a live web socket to the server which will receive messages in near real time when a new main tree hash is committed. The requester can use this information to keep a local fully replicated copy of the server main Merkle tree.

#### Response messages

````json
{
    "version": "1",
	"mth": "...url...",
    "ith": "...base64-encoded...",
    "kid": "xxx",
    "signature": "...base64-encoded...",
    "timestamp": "2021-04-13T15:22:23.535937Z"
}
````

### Signed main tree hash

````json
{
    "data": "...url...",
    "kid": "xxx",
    "timestamp": "2021-04-13T15:22:23.535937Z",
    "typ": "mth",
    "version": "1"
}
````

### Request current Merkle head

````http request
GET /api/v1/mth/current HTTP/1.1

````

#### Response