const Hapi = require('hapi')
const Path = require('path')

const server = new Hapi.Server()

const plugins = [
  require('inert')
]

server.register(plugins, err => {
  if (err) {
    throw err
  }

  server.connection({
    host: process.env.HOST || 'localhost',
      port: process.env.PORT || 5000,
      routes: {
        cors: true
      }
  })

  server.route({
    method: 'GET',
    path: '/{path*}',
    handler: {
      directory: {
        path: Path.join(__dirname, 'build'),
        listing: false,
        index: true
      }
    }
  })

  server.start(err => {
    if (err) {
      throw err
    }

    console.log(`Server running at ${server.info.uri}`)
  })
})
