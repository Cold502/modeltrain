<template>
  <div class="page-container">
    <div class="iframe-container">
      <iframe
        src="http://localhost:7860"
        frameborder="0"
        class="llamafactory-iframe"
      ></iframe>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelTraining'
}
</script>

<style scoped>
.page-container {
  padding: 0;
}

.iframe-container {
  margin-top: 0;
  width: 100%;
  height: calc(100vh - 0px);
}

.llamafactory-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>