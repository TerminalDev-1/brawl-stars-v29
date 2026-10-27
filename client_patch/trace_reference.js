'use strict';
const log = (...args) => send(args.map(String).join(' '));
const libc = Process.getModuleByName('libc.so');
const inetAddr = new NativeFunction(libc.getExportByName('inet_addr'), 'uint32', ['pointer']);
Interceptor.attach(libc.getExportByName('connect'), {
  onEnter(args) {
    const a = args[1];
    if (a.readU16() !== 2) return;
    const port = (a.add(2).readU8() << 8) | a.add(3).readU8();
    if (port !== 9339) return;
    a.add(4).writeU32(inetAddr(Memory.allocUtf8String('127.0.0.1')));
    log('GAME CONNECT', args[0], '127.0.0.1:9339');
  },
});
const g = Process.findModuleByName('libg.so');
log('reference baseline ready', g === null ? 'not loaded yet' : g.base);
