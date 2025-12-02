from iiif_prezi3 import Manifest, KeyValueString, Collection
from csv import DictReader
import base64
import magic
import requests


class COSAWManifest:
    def __init__(self, row):
        self.row = row

    @staticmethod
    def _get_based(url):
        return base64.urlsafe_b64encode(url.encode()).decode()

    @staticmethod
    def detect_mime_from_url(url):
        head = requests.head(url, allow_redirects=True)
        content_type = head.headers.get("Content-Type")

        if content_type and content_type != "application/octet-stream":
            return content_type

        # fallback: sniff bytes
        resp = requests.get(url, stream=True)
        data = resp.raw.read(2048)

        return magic.Magic(mime=True).from_buffer(data)

    def make_metadata(self):
        return [
            KeyValueString(
                label="Extent",
                value=self.row["Extent"],
            ),
            KeyValueString(
                label="Date",
                value=self.row["Date"],
            )
        ]

    def build(self):
        based = self._get_based(self.row['url'])
        identifier = row['url'].replace(
            "https://oaktrust.library.tamu.edu/bitstreams/",
            "").replace(
            "/download",
            ""
        )
        metadata = self.make_metadata()
        manifest_id = f"https://tamulib-dc-labs.github.io/cosaw-manifests/manifests/{identifier}"
        manifest = Manifest(
            id=f"{manifest_id}.json",
            label=row["Title"],
            metadata=metadata,
            rights=row["Rights"],
            behavior="paged"
        )
        pages = int(self.row["Extent"].split(' pages')[0])
        i = 1
        while i <= pages:
            canvas = manifest.make_canvas_from_iiif(
                url=f"https://api.library.tamu.edu/iiif/2/{based};{i}/info.json",
                id=f"{manifest_id}/canvas/{i}",
                label=f"PDF Page {i}",
                anno_id=f"{manifest_id}/annotation/{i}",
                anno_page_id=f"{manifest_id}/anno_page/{i}",
            )
            canvas.create_thumbnail_from_iiif(url=f"https://api.library.tamu.edu/iiif/2/{based};{i}/info.json")
            i += 1
        x = manifest.json(indent=4)
        with open(f"manifests/{identifier}.json", 'w') as f:
            f.write(x)
        return f"{manifest_id}.json", row["Title"],


if __name__ == "__main__":
    with open('cosaw.csv', 'r') as f:
        reader = DictReader(f)
        collection = Collection(
            id="https://tamulib-dc-labs.github.io/cosaw-manifests/collections.json",
            label="COSAW Bulletins",
            type="Collection"
        )
        for row in reader:
            if row['Is 200'] == 'y':
                x = COSAWManifest(row)
                data = x.build()
                collection.make_manifest(
                    id=data[0],
                    label=data[1],
                    type="Manifest"
                )
        y = collection.json(indent=4)
        with open("collections.json", 'w') as f:
            f.write(y)
