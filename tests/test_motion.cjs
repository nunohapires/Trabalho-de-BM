// Sem dependências: node tests/test_motion.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/pump_motion.js'), 'utf8');
const motion = vm.runInNewContext(source + '\nPumpMotion');
const distance = (a, b) => Math.hypot(a.x-b.x, a.y-b.y);
const near = (a, b) => assert.ok(Math.abs(a-b) < 1e-8, `${a} != ${b}`);
let up = 0, down = 0;
for (let i=0; i<=1440; i++) {
  const angle = i*Math.PI/720, pose = motion.at(angle);
  near(distance(pose.pin, motion.shaft), motion.crank);
  near(distance(pose.joint, pose.pin), motion.pitman);
  near(distance(pose.joint, motion.pivot), motion.rear);
  assert.ok(pose.fraction >= 0 && pose.fraction <= 1);
  assert.ok(pose.carrierY > motion.pivot.y && pose.carrierY < 332);
  assert.ok(!(pose.standingOpen && pose.travelingOpen));
  if (!pose.reversing) {
    const next = motion.at(angle+.00001);
    assert.equal(next.carrierY < pose.carrierY, pose.up);
    assert.equal(pose.standingOpen, pose.up);
    assert.equal(pose.travelingOpen, !pose.up);
    pose.up ? up++ : down++;
  }
}
assert.ok(up > 500 && down > 500);
near(motion.at(0).carrierY, motion.at(2*Math.PI).carrierY);
console.log('OK: ciclo completo, articulações rígidas, cabo vertical e sequência das válvulas.');
