const hello = require('../src/index');

test('hello function returns Hello World', () => {
    expect(hello()).toBe("Hello World");
});
