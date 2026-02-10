const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send('Hello World from Frontend!');
});

app.listen(port, () => {
    console.log(`Frontend app listening on port ${port}`);
});

function hello() {
    return "Hello World";
}

module.exports = hello;
