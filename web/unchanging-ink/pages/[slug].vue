<template>
  <pre>{{ mth }}</pre>
</template>
<script setup>
import { decodeFirst } from 'cbor'
import { onMounted, shallowRef } from 'vue'
import { TimestampService } from '~/utils/uits'

const UiTs = shallowRef(null)
const { params } = useRoute()
const runtimeConfig = useRuntimeConfig()

const { data: mth } = await useAsyncData(
  `mth-${params.slug}`,
  async () => {
    const serverService = new TimestampService(
      runtimeConfig.public.authority
    )
    const response = await fetch(
      `${serverService.baseUrl}v1/mth/${params.slug}`,
      {
        headers: {
          Accept: 'application/cbor',
        },
      }
    )
    if (response.ok) {
      const buffer = await response.arrayBuffer()
      return await decodeFirst(new Uint8Array(buffer))
    }
    return null
  }
)

onMounted(() => {
  UiTs.value = new TimestampService(window.location.origin)
})
</script>
