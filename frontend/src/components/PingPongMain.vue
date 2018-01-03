<template>
  <b-container fluid>
    <h1>{{ title }}</h1>
    <div v-if="!isLoading">
      <h3 class="text-xs-left">Total Matches: {{ totalMatches }}</h3>
      <b-table hover :items="scoreboard"></b-table>
      <b-row>
        <b-col>
          <h3 class="text-xs-left">Ranking</h3>
          <b-table hover :items="leaderboard"></b-table>
        </b-col>
        <b-col>
          <h3 class="text-xs-left">Recent matches</h3>
          <b-table hover :items="matches"></b-table>
        </b-col>
      </b-row>
    </div>
    <CustomSpinner v-if="isLoading" :style="{ margin: 'auto' }"/>
  </b-container>
</template>

<script>
import CustomSpinner from '@/components/CustomSpinner'
import axios from 'axios'

var BASE_URL = 'https://pingpong-slackbot.herokuapp.com'
if (process.env.NODE_ENV === 'development') {
  BASE_URL = 'http://127.0.0.1:5000'
}

export default {
  name: 'PingPongMain',
  components: {
    CustomSpinner
  },
  data () {
    return {
      leaderboard: [],
      loading: [true, true, true],
      matches: [],
      scoreboard: [],
      title: 'Cognite Ping Pong Leaderboard',
      totalMatches: 0
    }
  },
  created: function () {
    this.update()
  },
  computed: {
    isLoading () {
      var isLoading = false
      this.loading.forEach(function (l) {
        if (l) {
          isLoading = true
        }
      })
      return isLoading
    }
  },
  methods: {
    update () {
      this.getStats()
      this.getLeaderboard()
      this.getMatches()
      var self = this
      setTimeout(function () { self.update() }, 180000)
    },
    getStats () {
      var self = this
      var url = BASE_URL + '/scoreboard'
      axios.get(url)
        .then(function (response) {
          self.scoreboard = response.data.scoreboard
          self.totalMatches = response.data.total_matches
          self.loading.splice(0, 1, false)
        })
        .catch(function (error) {
          console.log(error)
        })
    },
    getLeaderboard () {
      var self = this
      var url = BASE_URL + '/leaderboard'
      axios.get(url)
        .then(function (response) {
          self.leaderboard = response.data.leaderboard
          self.loading.splice(1, 1, false)
        })
        .catch(function (error) {
          console.log(error)
        })
    },
    getMatches () {
      var self = this
      var url = BASE_URL + '/matches'
      axios.get(url)
        .then(function (response) {
          self.matches = response.data.matches
          self.loading.splice(2, 1, false)
        })
        .catch(function (error) {
          console.log(error)
        })
    }
  }
}
</script>
