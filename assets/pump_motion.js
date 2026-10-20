/* Geometria ilustrativa fixa: mecanismo plano de quatro barras, em pixels.
   As dimensões de campo continuam nos cartões; não se calibra uma unidade real. */
const PumpMotion = (() => {
  const pivot = {x: 300, y: 170}, shaft = {x: 165, y: 300};
  const crank = 40, pitman = 140, rear = 130, horsehead = 230;

  function linkage(angle) {
    const pin = {x: shaft.x + crank * Math.cos(angle), y: shaft.y + crank * Math.sin(angle)};
    const dx = pin.x - pivot.x, dy = pin.y - pivot.y, distance = Math.hypot(dx, dy);
    const along = (rear * rear - pitman * pitman + distance * distance) / (2 * distance);
    const normal = Math.sqrt(rear * rear - along * along);
    const joint = {x: pivot.x + along * dx / distance - normal * dy / distance,
      y: pivot.y + along * dy / distance + normal * dx / distance};
    const beamAngle = Math.atan2(pivot.y - joint.y, pivot.x - joint.x);
    return {pin, joint, beamAngle, carrierY: 230 + horsehead * beamAngle};
  }
  const positions = Array.from({length: 1440}, (_, i) => linkage(i * Math.PI / 720).carrierY);
  const top = Math.min(...positions), bottom = Math.max(...positions);

  function at(angle) {
    const pose = linkage(angle);
    const velocity = (linkage(angle + .0001).carrierY - linkage(angle - .0001).carrierY) / .0002;
    const reversing = Math.abs(velocity) < 1;
    return {...pose, fraction: Math.max(0, Math.min(1, (pose.carrierY - top) / (bottom - top))),
      up: velocity < 0, reversing, standingOpen: !reversing && velocity < 0,
      travelingOpen: !reversing && velocity > 0};
  }
  return {at, pivot, shaft, crank, pitman, rear, horsehead};
})();
