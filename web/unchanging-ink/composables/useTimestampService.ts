import type { Ref } from "vue"
import { TimestampService } from "~/utils/uits"

export function useTimestampService(authority: string): Ref<TimestampService> {
  const ts = ref<TimestampService>(new TimestampService(authority))

  onMounted(() => {
    ts.value.openLiveConnection()
  })
  onUnmounted(() => {
    ts.value.closeLiveConnection()
  })

  return ts as any as Ref<TimestampService>
}
