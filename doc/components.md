# Components

````
world --- proxy (nginx HTTP proxy)  ---[path: /api]---  backend (sanic)  --- --- db (postgres)
            |                                                               X
            |                                           worker (Python)  --- --- redis
            |                                                                  / ??
            +---  ---  ---  --- --- ---[path: /]--- --- frontend (nuxt)  --- /
````

## Backend

The main backend is a REST API written in Python sanic mounted on `/api`. It connects to a postgres database for storage and redis for PubSub.

The backend performs three functions:

1. Create signed timestamps and submit the `st` into the database for inclusion in the next interval. It can then wait for the inclusion proof and serve it from the database
2. Serve the main Merkle tree and provide intermediate proofs upon request.
3. Provide a live log stream of the main Merkle tree via websocket.

The backend can be horizontally scaled without limits.

Functions 1 and 3 essentially have to wait for the next interval and `mth` computation. They could poll the database. Function 3 already uses redis PubSub (and basically just copies from the message reception onto the websocket). Do we *have* to use a redis connection per concurrent client? Function 1 may accumulate a couple thousand clients waiting for their inclusion proofs, and function 3 may serve many hundred website users (and monitors) simultaneously.

***Question/Idea***: Can we have just one redis connection per process (thread?) and then use in-process messaging to fan out? The signal from redis is basically a synchronization broadcast. Function 1 will still need to hit the database, but wouldn't need to poll.

## Worker

The worker is a single Python process and the main source of interval tree computation. Every few seconds it creates a new interval tree from all `st` in the database that are not yet added to an interval, computes the interval tree hash, updates the main Merkle tree and signed main Merkle tree hash, and stores the inclusion proofs in the database. It announces a new `mth` via redis PubSub on channel `mth-live`.

The worker must be a single component, and needs to have enough processing power to compute all the hashes and signatures involved.

## Frontend

The frontend is a Nuxt.js application that combines both server-side pre-rendering and client-side updates. The pre-rendering may use the official API, the client-side updates can only use the official API. The Javascript (Vue.js) client connects to the websocket endpoint on the backend for live updates.

***Open point***: Have the pre-renderer connect to redis to fetch the current `mth` directly and more efficiently?

