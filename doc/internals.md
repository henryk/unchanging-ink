 * Input: data_x  (implicit: timestamp_x)
 * Set hash_x := sha512(CBOR(data_x, timestamp_x, typ, version))


 * set I_n := list of x  (that are not in I_{n-1})
 * calculate itmh_n as merkle tree head of list(hash_x for x in I_n)
 * for all x in I_n: set proof_x := calculate_proof(list(hash_x for x in I_n), x)


* set ith_n := {n, timestamp_n, itmh_n}
* commit new ith_n, calculate new mth_n
* announce mth_n, ith_n, consistency proof between mth_{n-1} and mth_n
