# unchanging.ink -- Merkle tree timestamping service

## Design rationale

The service provides signed timestamps for arbitrary submitted data, and allows public verification of the unchanged history of generated signatures. Cross timestamping with other timestamp services is possible, but not a core functionality. The design should allow for a very high rate of requests per second (at least a few thousand) to be usable on a large scale (f.e. operated by a government agency for an entire country).

### Goals

* Low barrier to integration, no registration necessary
* Provide signed timestamp
* (Optional) provide proof of integration in immutable log, within a reasonable time (<~5s)
* Public verification of the immutability property of the log
* Public (optionally offline) verification of inclusion proofs
* Can sustain > 1k requests/s

### Non-goals

* Cannot be used as a storage service: Input data is never returned
* Cannot provide proof of completeness (enumerate all data signed),
  cannot provide proof of non-inclusion (that some data was never signed)
* Inclusion proofs can have variable size, offloads some storage burden to claimant
* Inclusion proofs are *not* permanently stored server side
* Inclusion proof can have variable issuance time, are not instant

## Theory of operation

1. Signed timestamps (`st`) are the smallest unit: Signature over current time and arbitrary data.
2. Multiple `st` will be combined into an `interval`, each covering a certain, short, time window, typically 1s - 5s.
3. All `st` in an `interval` are combined into a binary Merkle tree (interval tree), yielding its root as the interval tree hash (`ith`).
4. The path from `st` to `ith` serves as proof of inclusion for this `st`. The server will store the proof only for a limited amount of time (~1 day).
5. All `ith` are continuously appended to a binary Merkle tree (main tree). Its current root (main tree hash, `mth`) is signed by the server (`smth`) and provides a single snapshot of the entire history of the server. All `ith` are retained indefinitely.



