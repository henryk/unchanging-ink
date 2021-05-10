<template>
  <v-row justify="center" align="center">
    <v-col cols="12" sm="8" md="6">
      <v-card>
        <v-card-title class="headline">
          {{ $t('welcome') }}
        </v-card-title>
        <v-card-text style="height: 25em; overflow-y: hidden">
          <v-timeline clipped>
            <transition-group name="slide-y-transition">
              <v-timeline-item
                v-for="item in items"
                :key="item"
                fill-dot
                color="primary"
                right
              >
                <v-card>
                  <v-card-text>Hash-Wert hier</v-card-text>
                </v-card>
                <template #icon>
                  <v-avatar
                    ><img src="@/assets/gibberish.svg" alt="#" /> </v-avatar
                ></template>
                <template #opposite>{{ item }}</template>
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
      items: [],
      cbHandle: null,
    }
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
    tick() {
      this.items.unshift(new Date().toISOString())
      if (this.items.length > 5) {
        this.items.pop()
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
