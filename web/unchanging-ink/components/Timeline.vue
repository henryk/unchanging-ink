<template>
  <v-card
    :loading="true"
    @mouseenter="pauseMover = true"
    @mouseleave="pauseMover = false"
  >
    <template #progress>
      <v-progress-linear :value="progressToNext"></v-progress-linear>
    </template>
    <v-card-title class="headline">
      {{ $t('liveView') }}
      <v-spacer></v-spacer>
      <v-icon v-if="paused">{{ mdiPause }}</v-icon
      ><v-icon v-else>{{ mdiPlay }}</v-icon>
    </v-card-title>
    <v-card-text style="max-height: 35em; overflow-y: hidden">
      <v-timeline v-show="items.length" clipped dense>
        <transition-group name="slide-y-transition">
          <timeline-item-card
            v-for="item in items"
            :key="item.time"
            :item="item"
          ></timeline-item-card>
        </transition-group>
      </v-timeline>
    </v-card-text>
  </v-card>
</template>

<script>
import { mdiPause, mdiPlay } from '@mdi/js'
import TimelineItemCard from './TimelineItemCard'

export default {
  name: 'TimelineCard',
  components: { TimelineItemCard },
  props: {
    estimatedNextTick: {
      type: Date,
      required: false,
      default: null,
    },
    averageTickDurationMillis: {
      type: Number,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      now: new Date(),
      nowInterval: null,
      mdiPause,
      mdiPlay,
      rawItems: [],
      pausedItems: [],
      pauseMover: false,
      pauseBackground: false,
    }
  },
  computed: {
    items() {
      return this.paused ? this.pausedItems : this.rawItems
    },
    paused() {
      return this.pauseMover || this.pauseBackground
    },
    progressToNext() {
      if (
        this.paused ||
        !this.estimatedNextTick ||
        !this.averageTickDurationMillis
      ) {
        return null
      }
      let diff =
        (this.estimatedNextTick - this.now) / this.averageTickDurationMillis
      if (diff < 0) {
        diff = 0
      }
      if (diff > 1.0) {
        diff = 1.0
      }
      diff = (1.0 - diff) * 100
      diff = (100.0 / 80.0) * diff - (20 * 100) / 80
      if (diff < 0) {
        diff = 0
      }
      return diff
    },
  },
  watch: {
    paused(newVal) {
      if (newVal) {
        this.pausedItems = [...this.rawItems]
      }
    },
  },
  mounted() {
    document.addEventListener(
      'visibilitychange',
      this.handleVisibilityChange,
      false
    )
    this.nowInterval = window.setInterval(this.nowHandler, 100)
  },
  beforeDestroy() {
    if (this.nowInterval !== null) {
      window.clearInterval(this.nowInterval)
      this.nowInterval = null
    }
  },
  methods: {
    handleVisibilityChange() {
      this.pauseBackground = document.hidden
    },
    nowHandler() {
      this.now = new Date()
    },
    tick(item) {
      this.rawItems.unshift(item)
      if (this.rawItems.length > 5) {
        this.rawItems.pop()
      }
    },
  },
}
</script>

<style scoped></style>
<i18n lang="yaml">
de:
  liveView: Live-Ansicht
en:
  liveView: Live View
</i18n>
