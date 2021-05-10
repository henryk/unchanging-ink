import Vue from 'vue'
import VueNativeSock from 'vue-native-websocket'

Vue.use(VueNativeSock, 'ws://localhost:23230/api/v1/mth/live', {
  format: 'json',
  reconnection: true,
})
