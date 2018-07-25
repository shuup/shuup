const path = require("path");
const fs = require("fs");

module.exports = function (bundler) {
    const rootDir = process.cwd();
    const outFile = path.resolve(rootDir, "generated_resources.txt");

    const readManifestJson = (maninfestPath) => {
        if (!fs.existsSync(maninfestPath)) {
            return [];
        }
        try {
            const resources = fs.readFileSync(maninfestPath, "utf8");
            return resources.split("\n");
        } catch (e) {
            return [];
        }
    };

    function processBundle(bundle, currentManinfest, basePath) {
        let output = bundle.name.replace(rootDir, "");

        if (output.startsWith(path.sep)) {
            output = output.substring(path.sep.length);
        }
        if (currentManinfest.indexOf(output) < 0) {
            currentManinfest.push(output);
        }
        bundle.childBundles.forEach(function (childBundle) {
            processBundle(childBundle, currentManinfest, basePath);
        });
    }

    bundler.on("bundled", (bundle) => {
        let maninfest = readManifestJson(outFile);
        processBundle(bundle, maninfest);
        // clear blank values
        maninfest = maninfest.filter(function (item) { return item; });
        fs.writeFileSync(outFile, maninfest.join("\n"));
    });
};
