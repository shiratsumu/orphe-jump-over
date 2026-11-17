// Node: replays the raw CSV through docs/jump.js and compares with ground truth
const fs = require('fs');
const { JumpDetector, SerialClock } = require('../docs/jump.js');
const [csv, gtPath] = process.argv.slice(2);
const lines = fs.readFileSync(csv, 'utf8').trim().split('\n');
const h = lines[0].split(','); const ix = k => h.indexOf(k);
const det = new JumpDetector(), clk = new SerialClock();
const out = [];
for (const L of lines.slice(1)) {
  const c = L.split(',').map(Number);
  const t = clk.time(c[ix('serial')], c[ix('packet')]);
  const e = det.push(t, { x: c[ix('ax_g')], y: c[ix('ay_g')], z: c[ix('az_g')] },
    { w: c[ix('qw')], x: c[ix('qx')], y: c[ix('qy')], z: c[ix('qz')] });
  if (e && e.type !== 'takeoff') out.push(e);
}
const gt = fs.readFileSync(gtPath, 'utf8').trim().split('\n').slice(1).map(l => +l.split(',')[2]);
let mae = 0, j = 0;
for (const e of out) {
  if (e.type !== 'jump') { console.log(e.type, e.t.toFixed(2), e.reason || ''); continue; }
  const g = gt[j++]; mae += Math.abs(e.cm - g);
  console.log(`land ${e.t.toFixed(3)} flight ${e.flight.toFixed(3)} raw ${e.raw.toFixed(1)} cm ${e.cm.toFixed(1)} gt ${g}`);
}
console.log('jumps', j, 'MAE(in-sample calibrated)', (mae / j).toFixed(2));
