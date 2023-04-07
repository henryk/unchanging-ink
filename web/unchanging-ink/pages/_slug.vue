<template>
  <pre>{{ mth }}</pre>
</template>
<script>
import { decodeFirst } from 'cbor'
import { TimestampService } from '~/utils/uits'

export default {
  async asyncData({ params }) {
    const UiTs = new TimestampService(process.env.AUTHORITY)
    const response = await fetch(`${UiTs.baseUrl}v1/mth/${params.slug}`, {
      headers: {
        Accept: 'application/cbor',
      },
    })
    let mth = null
    if (response.ok) {
      const data = await response.body
      mth = await decodeFirst(data)
    }
    return {
      mth,
      UiTs,
    }
  },
  mounted() {
    this.UiTs = new TimestampService(window.location.origin)
  },
  beforeDestroy() {
    delete this.UiTs
  },
}
</script>
