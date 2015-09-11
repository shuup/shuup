var path = require("path");

function basifyFile(spec, file) {
    if (!spec.base) {
        return file;
    }
    return path.join(spec.base, file);
}

function basifyFiles(spec) {
    return spec.files.map(basifyFile.bind(null, spec));
}

module.exports.basifyFile = basifyFile;
module.exports.basifyFiles = basifyFiles;
