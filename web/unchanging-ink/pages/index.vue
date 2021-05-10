<template>
  <v-row justify="center" align="center">
    <v-col cols="12" sm="8" md="6">
      <v-card @mouseenter="pause" @mouseleave="unpause">
        <v-card-title class="headline">
          {{ $t('liveView') }}
          <v-spacer></v-spacer>
          <v-icon v-if="paused">mdi-pause</v-icon
          ><v-icon v-else>mdi-play</v-icon>
        </v-card-title>
        <v-card-text style="max-height: 35em; overflow-y: hidden">
          <v-timeline v-show="items.length" clipped>
            <transition-group name="slide-y-transition">
              <v-timeline-item
                v-for="item in items"
                :key="item.time"
                fill-dot
                color="primary"
                right
              >
                <v-card>
                  <v-card-text style="font-family: Roboto Mono, monospace">{{
                    item.hash
                  }}</v-card-text>
                </v-card>
                <template #icon>
                  <v-avatar
                    ><span
                      class="white--text"
                      style="
                        font-family: Roboto Mono, monospace;
                        line-height: 0.9;
                        white-space: pre-line;
                      "
                      >{{ item.icon }}</span
                    ></v-avatar
                  ></template
                >
                <template #opposite>{{ item.time }}</template>
              </v-timeline-item>
            </transition-group>
          </v-timeline>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
export default {
  data() {
    return {
      rawItems: [],
      pausedItems: [],
      paused: false,
      cbHandle: null,
    }
  },
  // eslint-disable-next-line require-await
  async fetch() {
    this.tick()
  },
  computed: {
    items() {
      return this.paused ? this.pausedItems : this.rawItems
    },
  },
  mounted() {
    this.cbHandle = window.setInterval(() => {
      return this.tick()
    }, 3000)
  },
  beforeDestroy() {
    if (this.cbHandle) {
      window.clearInterval(this.cbHandle)
      this.cbHandle = null
    }
  },
  methods: {
    pause() {
      this.pausedItems = [...this.rawItems]
      this.paused = true
    },
    unpause() {
      this.paused = false
    },
    tick() {
      const HEX_CHARS = '0123456789ABCDEF'
      const item = {
        time: new Date().toLocaleString(),
        hash: [...Array(64)]
          .map((_) =>
            HEX_CHARS.charAt(Math.floor(Math.random() * HEX_CHARS.length))
          )
          .join(''),
        icon: [...Array(3)]
          .map((_) =>
            [...Array(5)]
              .map((_) =>
                HEX_CHARS.charAt(Math.floor(Math.random() * HEX_CHARS.length))
              )
              .join('')
          )
          .join('\n'),
      }
      this.rawItems.unshift(item)
      if (this.rawItems.length > 5) {
        this.rawItems.pop()
      }
      return true
    },
  },
}
</script>
<style scoped>
.myfade-enter-active,
.myfade-leave-active {
  transition: height 0.25s;
}

.myfade-enter,
.fade-leave-to {
  height: 100%;
}
</style>
