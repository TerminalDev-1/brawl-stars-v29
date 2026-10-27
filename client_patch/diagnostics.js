// Read-only crash instrumentation: preserve the original failure behavior.
'use strict';

const androidLog = new NativeFunction(
  Process.getModuleByName('liblog.so').getExportByName('__android_log_write'),
  'int', ['int', 'pointer', 'pointer']);
const tag = Memory.allocUtf8String('v29-diagnostic');
const log = (...args) => {
  const message = args.map(String).join(' ');
  androidLog(4, tag, Memory.allocUtf8String(message));
};
log('script entered');

function describe(address) {
  const module = Process.findModuleByAddress(address);
  return module === null ? address.toString() :
    module.name + '+' + address.sub(module.base) + ' (' + address + ')';
}

function capture(label, context) {
  log(label, 'thread', Process.getCurrentThreadId(),
      'lr', describe(context.lr), 'pc', describe(context.pc));
  for (const mode of [Backtracer.ACCURATE, Backtracer.FUZZY]) {
    try {
      log('backtrace', mode, Thread.backtrace(context, mode).map(describe).join('\n'));
    } catch (error) {
      log('backtrace error', String(error));
    }
  }
  try {
    log('stack', hexdump(context.sp, { length: 256, ansi: false }));
  } catch (error) {
    log('stack error', String(error));
  }
}

const libc = Process.getModuleByName('libc.so');
const guard = libc.findExportByName('__stack_chk_guard');
log('stack guard', guard, guard === null ? '' : guard.readPointer());
Process.setExceptionHandler(details => {
  log('native exception', details.type, details.address,
      JSON.stringify(details.context));
  return false;
});
Interceptor.attach(libc.getExportByName('sleep'), {
  onEnter(args) {
    this.caller = this.returnAddress;
    this.guard = guard === null ? null : guard.readPointer();
    log('sleep enter', args[0].toUInt32(), 'caller', describe(this.caller),
        'guard', this.guard);
  },
  onLeave() {
    log('sleep leave', describe(this.caller), 'guard',
        guard === null ? '' : guard.readPointer(), 'previous', this.guard);
  },
});
for (const name of ['__stack_chk_fail', '__fortify_fatal', 'abort']) {
  const address = libc.findExportByName(name);
  if (address !== null) {
    Interceptor.attach(address, {
      onEnter() { capture(name, this.context); },
    });
    log('attached', name, address);
  }
}
log('ready; messaging hooks disabled');
