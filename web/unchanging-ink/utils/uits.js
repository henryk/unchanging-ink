import { sleep } from './misc'

const DEFAULT_OPTIONS_GET_TIMESTAMP = {
  wait: false,
  maxRetries: 5,
  // eslint-disable-next-line require-await
  firstStepCallback: async () => null,
}

const DEFAULT_OPTIONS_VERIFY_TIMESTAMP = {
  online: true,
}

// Case-sensitive v1
const COMPACT_TS_RE =
  /^(?<authority>(?:[hH][tT][tT][pP][sS]?:\/\/)?[[\]0-9a-z_.:-]+(?::[0-9]+)?)\/(?<interval>[0-9]+)#v1(?=[:,])(?::(?<mth>[a-zA-Z0-9_-]+))?(?:,(?<timestamp>[^,]+),(?<proof>[a-zA-Z0-9_-]+))?$/

export function parseCompactTs(c) {
  const match = COMPACT_TS_RE.exec(c)
  if (match) {
    return { ...match.groups }
  }
}

function canonizeAuthority(s) {
  let retval = s.replace(/\/*$/, '')
  if (retval.toLowerCase().startsWith('https://')) {
    retval = retval.replace(/^https:\/\//i, '')
    if (retval.endsWith(':443')) {
      retval = retval.replace(/:443/, '')
    }
  }
  return retval.toLowerCase()
}

const SOURCE_DIRECT_SET = 'direct'

export class TimestampService {
  constructor(authority) {
    this.authority = canonizeAuthority(authority)
    this.baseUrl =
      (!this.authority.includes('://') ? 'https://' : '') +
      this.authority +
      '/api/'
    this.cacheIth = {}
    this.cacheMtree = {}
    this.knownHead = {
      interval: null,
      mth: null,
      source: null,
    }
    this.ws = null
    this.tickItems = []
    console.log(
      `Created new TimestampService for ${this.authority} at ${this.baseUrl}`
    )
  }

  openLiveConnection() {
    if (this.ws) {
      this.closeLiveConnection()
    }
    this.ws = new WebSocket(
      this.baseUrl.replace(/^http/i, 'ws') + 'v1/mth/live'
    )
    // FIXME reconnect?
    this.ws.onmessage = (event) => this._wsmessage(event)
  }

  _wsmessage(event) {
    const data = JSON.parse(event?.data ?? '')
    this.tick(data)
  }

  tick(data) {
    const item = {
      time: data?.timestamp ?? 'not set',
      hash: data?.mth ?? 'NOT SET',
      icon: (String(data?.interval) ?? '?').match(/.{1,3}/g).join('\n'),
    }
    if (data?.timestamp) {
      item.timeobj = new Date(data.timestamp)
      item.received = new Date()
    }
    this.tickItems.unshift(item)
    if (this.tickItems.length > 5) {
      this.tickItems.pop()
    }
    return true
  }

  get averageTickDurationMillis() {
    if (this.tickItems.length > 1) {
      return (
        (this.tickItems[0].received -
          this.tickItems[this.tickItems.length - 1].received) /
        this.tickItems.length
      )
    }
    return 1000.0
  }

  get estimatedNextTick() {
    return new Date(this.lastTick.getTime() + this.averageTickDurationMillis)
  }

  get lastTick() {
    if (this.tickItems && this.tickItems.length > 0) {
      return this.tickItems[0].received
    }
  }

  closeLiveConnection() {
    if (this.ws) {
      this.ws.close()
      delete this.ws
      this.ws = null
    }
  }

  setTrusted(url, source = SOURCE_DIRECT_SET) {
    const parsedUrl = parseCompactTs(url)
    if (parsedUrl) {
      this.knownHead = {
        interval: parseInt(parsedUrl.interval),
        mth: parsedUrl.mth,
        source,
      }
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  amendTree(extensionProof) {}

  async getTimestamp(data, options = DEFAULT_OPTIONS_GET_TIMESTAMP) {
    const request = { data }
    const options_ = { ...DEFAULT_OPTIONS_GET_TIMESTAMP, ...options }
    let response = await fetch(
      this.baseUrl + 'v1/ts/' + (options_.wait ? '?wait' : ''),
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
      }
    )
    let ts = null
    if (response) {
      ts = await response.json()
    }
    if (!response || !ts || !ts.id) {
      return null
    }
    if (ts && ts.proof) {
      return ts
    }
    await options_.firstStepCallback()
    let retryCounter = 0
    while (retryCounter < 5 && ts && !ts?.proof) {
      retryCounter++
      const waitTime = this.estimatedNextTick - new Date() + 1000
      await sleep(waitTime)
      response = await fetch(this.baseUrl + 'v1/ts/' + ts.id + '/', {
        headers: {
          Accept: 'application/json',
        },
      })
      if (response) {
        ts = await response.json()
      }
    }
    if (ts && ts.proof) {
      return ts
    }
    return null
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async verifyTimestamp(data, ts, options = DEFAULT_OPTIONS_VERIFY_TIMESTAMP) {}
}
