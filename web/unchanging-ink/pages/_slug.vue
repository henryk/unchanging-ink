<template>
  <pre>{{ mth }}</pre>
</template>
<script>
export default {
  async asyncData({ params }) {
    const mth = await fetch(`http://backend:8000/v1/mth/${params.slug}`, {
      headers: {
        Accept: 'application/json',
      },
    }).then((res) => res.json())
    return { mth }
  },
}
</script>
