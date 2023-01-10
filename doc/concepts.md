# Basic concepts

A (binary) Merkle tree is an append-only data structure, which stores (information about) a sequence of items ("leaf nodes", "leafs") and provides, at each point in time, a single cryptographic hash value ("root node", "root", or "head") committing to all items in the data structure. Each time a new leaf is appended a new head is calculated. Leafs can never be removed, only appended.

A Merkle tree allows for efficient (that is: in *log n*) communication and verification of two different basic types of proofs:

 * An **inclusion proof** proves, given a specific head, that a specific leaf is included in that head. This proves that the leaf, and its data, was present at the time that head was created. Multiple inclusion proofs are also strictly ordered, proving which leaf was appended earlier.
 * A **consistency proof** proves, given an 'old' and a 'new' head, that the old head represents a sequence of leafs that is a prefix of the sequence of leafs represented by the new head. This proves that the new head was created from the old head only by appending new leafs, and no old leaf was dropped or changed.
