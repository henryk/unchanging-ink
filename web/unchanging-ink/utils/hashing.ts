async function hashSha512(x: ArrayBuffer): Promise<string> {
  return (
    "sha512:" +
    Array.from(new Uint8Array(await crypto.subtle.digest("SHA-512", x)))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("")
  )
}

const HASH_METHODS = {
  async sha512(x: ArrayBuffer) {
    return await hashSha512(x)
  },
  // eslint-disable-next-line require-await
  async raw(x: ArrayBuffer) {
    const s = String(x)
    if (s.length <= 256) {
      return s
    }
    return null
  },
}

export async function computeHash(inputObj: CreateInput) {
  const hashMethod = HASH_METHODS[inputObj.hash]
  let hash = null
  if (inputObj?.text?.length) {
    hash = await hashMethod(new TextEncoder().encode(inputObj.text))
  } else if (inputObj?.files?.length) {
    const fileHashes = await Promise.all(
      Array.from(inputObj.files).map(
        async (file) => await hashMethod(await file.arrayBuffer()),
      ),
    )
    if (fileHashes.includes(null)) {
      return null
    }
    fileHashes.sort()
    hash = await hashMethod(
      new TextEncoder().encode(
        "[" + fileHashes.map((x) => `"${x}"`).join(", ") + "]",
      ),
    )
  }
  if (!hash) {
    return null
  }
  return hash
}
