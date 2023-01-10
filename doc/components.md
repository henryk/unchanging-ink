# Components

````
world --- proxy (nginx HTTP proxy)  ---[path: /api]---  backend (sanic)  --- --- db (postgres)
            |                                                               X
            |                                           worker (Python)  --- --- redis
            |                                                                  /
            +---  ---  ---  --- --- ---[path: /]--- --- frontend (nuxt)  --- /
````

## Backend

The main backend is a REST API written in Python sanic mounted on `/api`. It connects to a postgres database for storage and redis for PubSub and transient data caching.

The backend performs three functions:

1. Create timestamp and submit the `ts` into the database for inclusion in the next interval. It can then wait for the inclusion proof and serve it from the database
2. Serve the main Merkle tree and provide intermediate proofs upon request.
3. Provide a live log stream of the main Merkle tree via websocket.

The backend can be horizontally scaled without limits.

Functions 1 and 3 essentially have to wait for the next interval and `mth` computation. They could poll the database. Function 3 already uses redis PubSub (and basically just copies from the message reception onto the websocket). Function 1 may accumulate a couple thousand clients waiting for their inclusion proofs, and function 3 may serve many hundred website users (and monitors) simultaneously.

We're using one redis connection per process/thread and then use in-process messaging to fan out. The signal from redis is basically a synchronization broadcast. Function 1 will still need to hit the database, but won't need to poll.

## Worker

The worker is a single Python process and the main source of interval tree computation. Every few seconds it creates a new interval tree from all `pt` in the database that are not yet added to an interval, computes the interval tree hash, updates the main Merkle tree, and stores the inclusion proofs in the database. It announces a new `mth` via redis PubSub on channel `mth-live`.

The worker must be a single component, and needs to have enough processing power to compute all the hashes and signatures involved.

## Frontend

The frontend is a Nuxt.js application that combines both server-side pre-rendering and client-side updates. Both use the official API, but the pre-renderer may also hit redis directly. The Javascript (Vue.js) client connects to the websocket endpoint on the backend for live updates.

The pre-renderer connects to redis to fetch the current `mth` directly and more efficiently.

