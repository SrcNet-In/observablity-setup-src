const express = require('express');
const http = require('http');
const promClient = require('prom-client');

const collectDefaultMetrics = promClient.collectDefaultMetrics;
collectDefaultMetrics({ register: promClient.register });

const apiHits = new promClient.Counter({
    name: 'api_hits',
    help: 'Number of hits to the API',
});
const httpRequests = new promClient.Counter({
    name: 'http_requests',
    help: 'Number of HTTP requests',
    labelNames: ['route','method', 'status'],
});

const app = express();
const server = http.createServer(app);
server.listen(3000, () => {
    console.log('Server is running on port 3000');
});

app.get('/fast', (_, res) => {
    apiHits.inc();
    httpRequests.inc({ route: '/fast', method: 'GET', status: 200 });
    try{
        console.log('This is a fast request hit!');
        res.send('This is a fast request!');
    } catch (error) {
        logger.error('An error occurred!');
        res.status(500).send('An error occurred!');
    }
});

app.get('/slow', async(_, res) => {
    apiHits.inc();
    httpRequests.inc({ route: '/slow', method: 'GET', status: 200 });
    try {
        console.log('This is a slow request hit!');
        await new Promise(resolve => setTimeout(resolve, 3000));
        res.send('This is a slow request!');
    } catch (error) {
        logger.error('An error occurred!');
        res.status(500).send('An error occurred!');
    }
});

app.get('/metrics', async(_, res) => {
    console.log('This is a metrics request hit!');
    const metrics = await promClient.register.metrics();
    res.setHeader('Content-Type', promClient.register.contentType);
    res.send(metrics);
});