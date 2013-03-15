import urlparse, urllib
from dateutil.tz import tzlocal

class NotFound(ValueError):
    pass

class Links(object):
    def __init__(self, db):
        self.coll = db['links']
        
    def insertOrUpdate(self, doc):
        if not doc['href']:
            raise ValueError("no link")
        self.extract(doc)
        self.coll.update({'href':doc['href']}, doc, upsert=True, safe=True)

    def extract(self, doc):
        forUsers = []
        tags = []
        for t in doc.get('tag', '').split(' '):
            if t.startswith('for:'):
                forUsers.append(t[4:])
            else:
                tags.append(t)
        doc['extracted'] = dict(tags=tags, forUsers=forUsers)

    def find(self, uri):
        docs = list(self.coll.find({'href': uri}))
        if len(docs) == 0:
            raise NotFound("not found")
        elif len(docs) > 1:
            raise ValueError("%s docs found for href %s" % (len(docs), uri))
        else:
            return docs[0]
            
    def forDisplay(self, doc):
        """return a mustache-ready dict for this db doc"""
        out = doc.copy()
        del out['_id']
        out['t'] = out['t'].astimezone(tzlocal()).isoformat()
        if not out['description'].strip():
            out['displayDescription'] = out['href']
        else:
            out['displayDescription'] = out['description']

        out['tagWords'] = [{'word' : w} for w in out['tag'].split(None)]
        out['domain'] = urlparse.urlparse(out['href']).netloc
        out['editLink'] = 'addLink?' + urllib.urlencode([('url', out['href'])])
        out['shareWith'] = [{'label' : uri} for uri in doc.get('shareWith', [])]
        return out

    def fromPostdata(self, data, user, t):
        if not user or not data.href:
            raise ValueError("incomplete")
        return dict(
            user=user,
            description=data.description,
            extended=data.extended,
            href=data.href,
            private=data.private,
            shareWith=filter(None, data.shareWith.split(',')),
            tag=data.tag,
            t=t,
        )
