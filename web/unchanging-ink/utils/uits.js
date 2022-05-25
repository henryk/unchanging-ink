import { sleep } from './misc'

const DEFAULT_OPTIONS = {
  wait: false,
  maxRetries: 5,
  waitTimeEstimator: () => 1000,
  // eslint-disable-next-line require-await
  firstStepCallback: async () => null,
}

export class TimestampService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl
  }

  async getTimestamp(data, options = DEFAULT_OPTIONS) {
    const request = { data }
    const options_ = { ...DEFAULT_OPTIONS, ...options }
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
      const waitTime = options_.waitTimeEstimator()
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
}
