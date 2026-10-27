'use strict';
if (globalThis.V29_LIBRARY_PROFILE !== 'stock')
  throw new Error('trace_startup.js requires --client-libraries stock');
const log = (...args) => send(args.map(String).join(' '));
let game = null;
function where(p) {
  if (game !== null && p.compare(game.base) >= 0 && p.compare(game.base.add(game.size)) < 0)
    return 'libg+' + p.sub(game.base);
  return p.toString();
}
function traceGame() {
  if (game !== null) return;
  game = Process.findModuleByName('libg.so');
  if (game === null) return;
  log('GAME', game.base, game.size);
  for (const off of [0x10cb2c,0x4db7d8,0x296b10]) log('CODE', off.toString(16), hexdump(game.base.add(off), {length:32,ansi:false}));
  for (const imp of game.enumerateImports()) if (['sleep','sscanf','__stack_chk_fail'].includes(imp.name)) log('IMPORT', imp.name, imp.address, imp.slot);
  const singleton = game.base.add(0xc65648);
  for (const [name, offset] of [['singleton-init', 0xb48fc],
                                ['singleton-destroy', 0x3ee8dc],
                                ['startup', 0x375000]]) {
    Interceptor.attach(game.base.add(offset), {
      onEnter(args) {
        log(name, 'enter', 'caller', where(this.returnAddress),
            'object', singleton.readPointer(), 'args', args[0], args[1]);
      },
      onLeave(result) { log(name, 'leave', result, 'object', singleton.readPointer()); },
    });
  }
}
const libc = Process.getModuleByName('libc.so');
let scans = 0;
Interceptor.attach(libc.getExportByName('sscanf'), {
  onEnter(args) {
    if (game === null || !where(this.returnAddress).startsWith('libg+') || where(this.returnAddress) === 'libg+0x69da34' || scans++ > 35) return;
    try { log('sscanf', where(this.returnAddress), args[0].readUtf8String(),
              'format', args[1].readUtf8String(), 'dest', args[2], args[3]); }
    catch (e) { log('sscanf read error', e); }
  },
});
Interceptor.attach(libc.getExportByName('sleep'), {
  onEnter(args) { log('sleep', args[0].toUInt32(), 'caller', where(this.returnAddress)); },
});
Process.setExceptionHandler(details => {
  const c = details.context;
  log('EXCEPTION', details.type, where(c.pc), 'lr', where(c.lr),
      'r0', c.r0, 'r1', c.r1, 'r2', c.r2, 'sp', c.sp);
  return false;
});
Interceptor.attach(Process.getModuleByName('libdl.so').getExportByName('android_dlopen_ext'), {
  onEnter(args) { this.name = args[0].isNull() ? '' : args[0].readUtf8String(); },
  onLeave(result) {
    if (this.name.includes('libg.so')) { log('dlopen', this.name, result); traceGame(); }
  },
});
traceGame();
log('trace ready');
