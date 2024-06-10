import { Ref } from "vue"
import { TimestampService as _TimestampService } from "~/utils/uits"

export type TimestampService = Pick<_TimestampService, keyof _TimestampService>

export function useTimestampService(authority: string): Ref<TimestampService> {
  const ts = ref<TimestampService>(new _TimestampService(authority))

  onMounted(() => {
    ts.value.openLiveConnection()
  })
  onUnmounted(() => {
    ts.value.closeLiveConnection()
  })

  return ts
}
