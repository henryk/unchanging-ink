async function hashSha512(x) {
  return (
    'sha512:' +
    Array.from(new Uint8Array(await crypto.subtle.digest('SHA-512', x)))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  )
}

export async function computeHash(inputObj) {
  const hashMethod = {
    async sha512(x) {
      return await hashSha512(x)
    },
    async raw(x) {
      const s = String(x)
      if (s.length <= 256) {
        return s
      }
      return null
    },
  }[inputObj.hash]
  let hash = null
  if (inputObj?.text?.length) {
    hash = await hashMethod(new TextEncoder().encode(inputObj.text))
  } else if (inputObj?.files?.length) {
    const fileHashes = await Promise.all(
      Array.from(inputObj.files).map(
        async (file) => await hashMethod(await file.arrayBuffer())
      )
    )
    if (fileHashes.includes(null)) {
      return null
    }
    fileHashes.sort()
    hash = await hashMethod(
      new TextEncoder().encode(
        '[' + fileHashes.map((x) => `"${x}"`).join(', ') + ']'
      )
    )
  }
  if (!hash) {
    return null
  }
  return hash
}
