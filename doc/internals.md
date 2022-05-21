 * Input: data_x  (implicit: timestamp_x)
 * Set hash_x := sha3(CBOR(data_x, timestamp_x, typ, version))


 * set I_n := list of x  (that are not in I_{n-1})
 * calculate itmh_n as merkle tree head of list(hash_x for x in I_n)
 * for all x in I_n: set proof_x := calculate_proof(list(hash_x for x in I_n), x)


* set ith_n := {n, timestamp_n, itmh_n}
* commit new ith_n, calculate new mth_n
* announce mth_n, ith_n, consistency proof between mth_{n-1} and mth_n

````
    TIMESTAMP                                 INTERVAL

 ´-------------`                          ´´=============``
 |   data      |                          ||  interval   ||
´+-------------+`                         ||  timestamp  ||  SHA3  
||  timestamp  ||   SHA3                  ||  typ        +----------> ihash
||  typ        +------\                   ||  version    ||             |
||  version    ||     |              /--> ||  ith        ||             v
+`=============´+     |   *********  |    |`-------------`|          *********
|   hash        |  <--^-->* ITREE *--/    |   mth         | <------- * MTREE *
|   id          |         *********       |   proof       |          *********
|   proof       |                         `---------------´
+---------------+
.   tag         .
.................
````

**hash**: Hash of individual timestamp entry (contains `data` which is never stored anywhere)<br>
**tag**: Stored in database but not returned in any API<br>
**ITREE** (*interval tree*): Virtual merkle tree containing all **hash** of one interval. Not persisted anywhere.<br>
**ith** (*interval tree head*): head of **ITREE** for one interval

**ihash** (*interval hash*): Hash of interval (contains `ith`)<br>
**MTREE** (*main tree*): Main merkle tree, containing all **ihash** up to and including interval<br>
**mth** (*main tree head*): head of **MTREE** at the time of interval

External representation

dev.unchanging.ink/ts#v1:base64(cbor([interval,timestamp,a,path]))
