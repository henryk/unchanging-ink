<template>
  <pre>{{ mth }}</pre>
</template>
<script>
import { decodeFirst } from 'cbor'

export default {
  async asyncData({ params }) {
    const response = await fetch(`http://backend:8000/v1/mth/${params.slug}`, {
      headers: {
        Accept: 'application/cbor',
      },
    })
    if (response.ok) {
      const data = await response.body
      const mth = await decodeFirst(data)
      return { mth }
    }
    return {}
  },
}
</script>
