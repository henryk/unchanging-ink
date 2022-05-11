 * Input: data_x  (implicit: timestamp_x)
 * Set hash_x := sha512(CBOR(data_x, timestamp_x, typ, version))


 * set I_n := list of x  (that are not in I_{n-1})
 * calculate ith as merkle tree head of list(hash_x for x in I_n)
 * for all x in I_n: set proof_x := calculate_proof(list(hash_x for x in I_n), x)

````python
def calculate_proof(x: int, l: list[bytes]) -> Tuple[int, list[bytes]]
````