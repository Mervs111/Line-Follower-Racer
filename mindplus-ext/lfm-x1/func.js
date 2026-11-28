// Kode C++ yang dihasilkan tiap blok (nama method = opcode di index.js).
// Semua blok memakai satu objek `robot` (LineFollower) yang di-begin() paling awal di setup().
class Func {
    constructor(runtime) {
        this.runtime = runtime;
    }

    _init(generator) {
        generator.addInclude('LineFollower.h');
        generator.addObject('robot', 'LineFollower robot;');
        generator.addSetup('robot.begin', 'robot.begin();', 9);
    }

    // ---- persiapan & sensor
    init(generator) {
        this._init(generator);
        return '';
    }

    calibrate(generator, block, parameter) {
        this._init(generator);
        return `robot.calibrate(${parameter.MS.code}, ${parameter.MODE.code});\n`;
    }

    loadCalibration(generator) {
        this._init(generator);
        return 'robot.loadCalibration();\n';
    }

    isCalibrated(generator) {
        this._init(generator);
        return ['robot.isCalibrated()', generator.ORDER_ATOMIC];
    }

    lineColor(generator, block, parameter) {
        this._init(generator);
        return `robot.setLineColor(${parameter.COLOR.code});\n`;
    }

    position(generator) {
        this._init(generator);
        return ['robot.position()', generator.ORDER_ATOMIC];
    }

    lineDetected(generator) {
        this._init(generator);
        return ['robot.lineDetected()', generator.ORDER_ATOMIC];
    }

    junction(generator) {
        this._init(generator);
        return ['robot.junction()', generator.ORDER_ATOMIC];
    }

    branch(generator, block, parameter) {
        this._init(generator);
        const fn = parameter.SIDE.code === 'right' ? 'branchRight' : 'branchLeft';
        return [`robot.${fn}()`, generator.ORDER_ATOMIC];
    }

    sensorValue(generator, block, parameter) {
        this._init(generator);
        return [`robot.sensorValue(${parameter.N.code})`, generator.ORDER_ATOMIC];
    }

    // ---- gerak
    follow(generator, block, parameter) {
        this._init(generator);
        return `robot.follow(${parameter.SPEED.code}, ${parameter.KP.code}, ${parameter.KD.code});\n`;
    }

    motor(generator, block, parameter) {
        this._init(generator);
        return `robot.motor(${parameter.L.code}, ${parameter.R.code});\n`;
    }

    stop(generator) {
        this._init(generator);
        return 'robot.stop();\n';
    }

    forward(generator, block, parameter) {
        this._init(generator);
        return `robot.forwardMm(${parameter.SPEED.code}, ${parameter.MM.code});\n`;
    }

    turnDegrees(generator, block, parameter) {
        this._init(generator);
        return `robot.turnDegrees(${parameter.SPEED.code}, ${parameter.DEG.code});\n`;
    }

    turnToLine(generator, block, parameter) {
        this._init(generator);
        const left = parameter.SIDE.code === 'right' ? 'false' : 'true';
        return `robot.turnToLine(${left}, ${parameter.SPEED.code});\n`;
    }

    // ---- path planning per indeks
    setPid(generator, block, parameter) {
        this._init(generator);
        return `robot.setPID(${parameter.KP.code}, ${parameter.KD.code});\n`;
    }

    runIndex(generator, block, parameter) {
        this._init(generator);
        // warna "hitam" = true di menu; runIndex() menerima whiteLine, jadi dibalik
        const white = parameter.COLOR.code === 'false' ? 'true' : 'false';
        return `robot.runIndex(${parameter.TRIG.code}, ${parameter.ACT.code}, ${parameter.SPEED.code}, ` +
            `${parameter.MM.code}, ${white});  // indeks ${parameter.N.code}\n`;
    }

    routeReset(generator) {
        this._init(generator);
        return 'robot.routeReset();\n';
    }

    blockNode(generator, block, parameter) {
        this._init(generator);
        return `robot.blockNode(${parameter.X.code}, ${parameter.Y.code});\n`;
    }

    clearBlocked(generator) {
        this._init(generator);
        return 'robot.clearBlockedNodes();\n';
    }

    shortestRoute(generator, block, parameter) {
        this._init(generator);
        const p = parameter;
        return `robot.runShortestRoute(${p.COLS.code}, ${p.ROWS.code}, ${p.SX.code}, ${p.SY.code}, ${p.HEAD.code}, ` +
            `${p.GX.code}, ${p.GY.code}, ${p.SPEED.code});\n`;
    }

    // ---- lain-lain
    battery(generator) {
        this._init(generator);
        return ['robot.batteryVoltage()', generator.ORDER_ATOMIC];
    }

    batteryLow(generator) {
        this._init(generator);
        return ['robot.batteryLow()', generator.ORDER_ATOMIC];
    }

    beep(generator, block, parameter) {
        this._init(generator);
        return `robot.beep(${parameter.MS.code});\n`;
    }

    button(generator, block, parameter) {
        this._init(generator);
        return [`robot.buttonPressed(${parameter.BTN.code})`, generator.ORDER_ATOMIC];
    }

    waitButton(generator, block, parameter) {
        this._init(generator);
        return `while (!robot.buttonPressed(${parameter.BTN.code})) {\n  yield();\n}\n`;
    }

    distance(generator) {
        this._init(generator);
        return ['robot.distanceMm()', generator.ORDER_ATOMIC];
    }

    resetDistance(generator) {
        this._init(generator);
        return 'robot.resetEncoders();\n';
    }
}

export default Func;
