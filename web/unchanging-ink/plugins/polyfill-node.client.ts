import { Buffer } from 'buffer';

export default defineNuxtPlugin(nuxtApp => {
    if (!globalThis.Buffer) {
        globalThis.Buffer = Buffer;
    }
})

