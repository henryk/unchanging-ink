import { Buffer } from 'buffer'

/**
 * Polyfill for Node.js Buffer API in the browser.
 * Required for cryptographic operations in utils/hashing.js and utils/uits.js
 * which use Buffer.from() and Buffer.concat() for handling binary data,
 * base64 encoding/decoding, and timestamp proof verification.
 */
export default defineNuxtPlugin(() => {
  if (!globalThis.Buffer) {
    globalThis.Buffer = Buffer
  }
})
