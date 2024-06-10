import { Buffer } from "buffer"

export interface TickItemDisplay {
  time: string
  hash: Base64String
  icon: string
  timeobj: Date
  received: Date
}

interface MainTreeConsistencyProof {
  old_interval: number
  new_interval: number
  nodes: Base64String[]
  version: "1"
}

interface MainTreeInclusionProof {
  head: number
  leaf: number | null
  a: number
  nodes: Base64String | null
  version: "1"
}

interface Interval {
  index: number
  timestamp: ConcreteTime
  ith: Base64String
  version: "1"
  typ: "it"
}

interface MainHeadWithConsistency {
  authority: string
  interval: Interval
  mth: Base64String
  version: "1"
  inclusion: MainTreeInclusionProof | null
  consistency: MainTreeConsistencyProof | null
}

type Base64String = string & { __brand: "base64" }
type ConcreteTime = string & { __brand: "isotime" }

class InconsistencyError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "InconsistencyError"
  }
}

class TimestampServerError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "TimestampServerError"
  }
}

// Case-sensitive v1
const COMPACT_TS_RE =
  /^(?<authority>(?:[hH][tT][tT][pP][sS]?:\/\/)?[[\]0-9a-z_.:-]+(?::[0-9]+)?)\/(?<interval>[0-9]+)#v1(?=[:,])(?::(?<mth>[a-zA-Z0-9_-]+))?(?:,(?<timestamp>[^,]+),(?<proof>[a-zA-Z0-9_-]+))?$/

interface TimeStampExtV1 {
  authority: string
  interval: string
  mth: Base64String | null
  timestamp: string | null
  proof: Base64String | null
}

export function parseCompactTs(c: string): TimeStampExtV1 | null {
  const match = COMPACT_TS_RE.exec(c)
  if (match) {
    // @ts-ignore
    return { ...match.groups } as TimeStampExtV1
  }
  return null
}

interface UpdateInput {
  mh: MainHeadWithConsistency | null
  received: Date
}

function canonizeAuthority(s: string) {
  if (!s) {
    return
  }
  let retval = s.replace(/\/*$/, "")
  if (retval.toLowerCase().startsWith("https://")) {
    retval = retval.replace(/^https:\/\//i, "")
    if (retval.endsWith(":443")) {
      retval = retval.replace(/:443/, "")
    }
  }
  return retval.toLowerCase()
}

export class TimestampService {
  private readonly cacheIth: { [key: number]: Buffer }
  private readonly cacheMtree: { [key: string]: Buffer }
  private knownHead: { mth: Buffer; interval: number } | null
  private ws: WebSocket | null
  private readonly _listeners: {
    [key: number]: (item: TickItemDisplay) => void
  }
  private _listener_next_idx: number

  public readonly authority: string
  public readonly baseUrl: string
  public readonly tickItems: TickItemDisplay[]

  constructor(authority: string) {
    this.authority = canonizeAuthority(authority)!
    this.baseUrl =
      (!this.authority.includes("://") ? "https://" : "") +
      this.authority +
      "/api/"
    this.cacheIth = {}
    this.cacheMtree = {}
    this.knownHead = null
    this.ws = null
    this.tickItems = []
    this._listeners = {}
    this._listener_next_idx = 0
    console.log(
      `Created new TimestampService for ${this.authority} at ${this.baseUrl}`,
    )
  }

  /* region Tick statistics */
  get averageTickDurationMillis() {
    const diffs = this.tickItems
      .slice(1)
      .map(
        (v, i) => this.tickItems[i].received.getTime() - v.received.getTime(),
      )
      .filter((v) => v >= 1000)
    if (diffs.length > 0) {
      return diffs.reduce((partial, v) => partial + v, 0) / diffs.length
    }
    return 5000.0
  }

  get estimatedNextTick() {
    const lastTick = this.lastTick
    if (!lastTick) {
      return null
    }
    return new Date(lastTick.getTime() + this.averageTickDurationMillis)
  }

  get lastTick() {
    if (this.tickItems && this.tickItems.length > 0) {
      return this.tickItems[0].received
    }
    return null
  }

  /* endregion */

  /* region Tick listeners */

  public addListener(f: (item: TickItemDisplay) => void) {
    this._listeners[this._listener_next_idx] = f
    this._listener_next_idx++
  }

  public removeListener(idx: number) {
    delete this._listeners[idx]
  }

  callListeners(item: TickItemDisplay) {
    for (const listener of Object.values(this._listeners)) {
      listener(item)
    }
  }

  /* endregion */

  /* region WebSocket management */

  openLiveConnection() {
    if (this.ws) {
      this.closeLiveConnection()
    }
    this.ws = new WebSocket(
      this.baseUrl.replace(/^http/i, "ws") + "v1/mth/live",
    )
    this.ws.onmessage = (event) => this._wsmessage(event)
    this.ws.onclose = (event) => this._wsclose(event)
  }

  _wsmessage(event: MessageEvent) {
    const data = JSON.parse(event?.data ?? "")
    this.tick(data)
  }

  _wsclose(event: CloseEvent) {
    // FIXME multiple retries?
    console.log("Live socket is closed, trying to reconnect in 10s")
    this.closeLiveConnection()
    setTimeout(() => {
      this.openLiveConnection()
    }, 10000)
  }

  closeLiveConnection() {
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
  }

  /* endregion */

  tick(mh: MainHeadWithConsistency, preload = false) {
    const item: TickItemDisplay = {
      time: mh.interval.timestamp ?? "not set",
      hash: mh.mth,
      icon: (String(mh.interval.index).match(/.{1,3}/g) || [""]).join("\n"),
      timeobj: new Date(mh.interval.timestamp),
      received: preload ? new Date(mh.interval.timestamp) : new Date(),
    }

    this.updateState(mh.authority, "mh", {
      mh,
      received: item.received,
    })

    this.tickItems.unshift(item)
    if (this.tickItems.length > 5) {
      this.tickItems.pop()
    }
    this.callListeners(item)
    return true
  }

  updateState(authority: string, type: "mh" | "mth", data: UpdateInput) {
    if (canonizeAuthority(authority) !== this.authority) {
      throw new InconsistencyError("Authority mismatch")
    }
    if (type === "mh") {
      const mh = data.mh!
      if (
        !this.knownHead?.interval ||
        this.knownHead.interval < mh.interval.index
      ) {
        this.knownHead = {
          interval: mh.interval.index,
          mth: Buffer.from(mh.mth, "base64"),
        }
      }
      this.cacheIth[mh.interval.index] = Buffer.from(mh.interval.ith, "base64")
      this.cacheMtree[`0-${mh.interval.index + 1}`] = Buffer.from(
        mh.mth,
        "base64",
      )
    }
  }
}
