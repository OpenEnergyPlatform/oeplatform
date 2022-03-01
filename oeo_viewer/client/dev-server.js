const { createServer } = require("http");
const { createProxyServer } = require("http-proxy");
const Path = require("path");
const Bundler = require("parcel-bundler");

const backEnd = {
  protocol: "http",
  host: "localhost",
  port: 5000
};

const parcelEnd = {
  protocol: "http",
  host: "localhost",
  port: 1234
};

// parcel options, such as publicUrl, watch, sourceMaps... none of which are needed for this proxy server configuration
const options = {};

// point parcel at its "input"
const entryFiles = Path.join(__dirname, "src", "index.html");

// init the bundler
const bundler = new Bundler(entryFiles, options);

bundler.serve();

// create a proxy server instance
const proxy = createProxyServer();

// serve
const server = createServer((req, res) => {
  if (req.url.includes("/api/")) {
    proxy.web(req, res, {
      // back-end server, local tomcat or otherwise
      target: backEnd,
      changeOrigin: true,
      autoRewrite: true
    });
  } else {
    // parcel's dev server
    proxy.web(req, res, {
      target: parcelEnd,
      ws: true
    });
  }
});

console.log("dev proxy server operating at: http://localhost:5050/");
server.listen(5050);
