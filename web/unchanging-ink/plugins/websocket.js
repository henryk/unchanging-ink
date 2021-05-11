import Vue from 'vue'
import VueNativeSock from 'vue-native-websocket'

const wsBasePath =
  (window.location.protocol === 'https' ? 'wss' : 'ws') +
  '://' +
  window.location.host

Vue.use(VueNativeSock, `${wsBasePath}/api/v1/mth/live`, {
  format: 'json',
  reconnection: true,
})
