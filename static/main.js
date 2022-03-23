var tweetCount = 1,
    page = 0,
    loading = false,
    bigArray = [];
const iosHeight = () => {
    document.documentElement.style.setProperty("--ios-height", window.innerHeight + "px");
};
window.addEventListener("resize", iosHeight);

window.onload = () => {
    //ios height
    iosHeight();
    const contwarn = document.querySelector("#contwarn");
    if (document.cookie.includes("always=true")) {
        contwarn.checked = true;
        forNow();
    }

    contwarn.addEventListener("change", () => {
        if (contwarn.checked) {
            document.cookie = `always = true; max-age=15780000; SameSite=None; Secure`;
        } else {
            document.cookie = "always=false";
        }
    })
}
function cookieTime() {
    document.querySelector("#contwarn").checked = true;
    document.cookie = `always = true; max-age=15780000; SameSite=None; Secure`;
    forNow();
}
function forNow() {
    document.querySelector("#block").style.display = "none";
    fetchNApply(page)
    page++;
    const tweetCont = document.querySelector(".tweetCont");
    tweetCont.onscroll = async () => {
        if (tweetCont.scrollTop > tweetCont.scrollHeight - tweetCont.offsetHeight - 100 && loading == false) {
            await fetchNApply(page);
            //console.log(page);
            page++;
        }
    };
}
function fetchNApply(page) {
    try {
        loading = true;
        fetch(`/api/latest/?tweets=10&page=${page}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(e => createTweet(e));
            })
            .then(setTimeout(() => loading = false, 500));
    } catch (error) {
        console.log(error);
        alert(error)
    }

}

function imgPrev(img) {
    const prevImgCont = document.querySelector('.previmgcont');
    img.addEventListener('click', () => {
        const clone = img.cloneNode(true);
        clone.removeAttribute("width");
        clone.removeAttribute("height");
        clone.className = "previmg";
        prevImgCont.innerHTML = "";
        prevImgCont.appendChild(clone);
        prevImgCont.style.display = '';
    });
}
/*
 cont ={
    inner: text
    src: link
    lazy: bool
    href: link
    video: link
 }
 */
function createEl(tag, cls, cont) {
    const el = document.createElement(tag);
    if (cls)
        el.className = cls;
    if (cont) {
        if (cont.inner)
            el.innerHTML = cont.inner;
        if (cont.src)
            el.src = cont.src;
        if (cont.lazy)
            el.setAttribute("loading", "lazy");
        if (cont.href)
            el.setAttribute("href", cont.href),
                el.setAttribute("rel", "noreferrer"),
                el.setAttribute("target", "_blank");
        if (cont.video) {
            el.setAttribute("preload", "auto");
            el.setAttribute("controls", "");
            el.setAttribute("disablePictureInPicture", "");
            el.setAttribute("webkit-playsinline", "");
            el.setAttribute("playsinline", "");
            const source = document.createElement("source");
            source.src = cont.video;
            source.setAttribute("type", "video/mp4");
            el.appendChild(source);
        }
    }
    return el;
}

function createTweet(json) {
    if (!bigArray.includes(json["tweet"])) {
        const tweet = createEl("div", "tweet");
        tweet.id = "t" + tweetCount;

        const auth = createEl("div", "auth");

        const aimage = createEl("img", "aimage", {
            src: json["pfp"],
            lazy: true
        });

        const aname = createEl("a", "aname", {
            href: `https://twitter.com/${json['screen_name']}`
        });

        aname.appendChild(createEl("div", undefined, {
            inner: json['uploader']
        }));

        aname.appendChild(createEl("div", undefined, {
            inner: "@" + json['screen_name']
        }));

        const type = createEl("a", "type", { inner: json["type"], href: json["tweet"] });

        auth.appendChild(aimage);
        auth.appendChild(aname);
        auth.appendChild(type);

        tweet.appendChild(auth);

        json["description"] = json["description"].replaceAll(/http.*t.co\S+/g, "");


        if (json["description"] != "") {
            const desc = createEl("div", "desc", { inner: json["description"] });
            tweet.appendChild(desc);
        }

        switch (json["type"]) {
            case "Text":
                //so empty
                break;
            case "Image":
                const media = createEl("img", "media", {
                    src: json["thumbnail"],
                    lazy: true
                });
                tweet.appendChild(media);
                break;
            case "Video":
                const video = createEl("video", "media", {
                    video: json["url"]
                });
                tweet.appendChild(video);
                break;
            default:
                const video2 = createEl("video", "media", {
                    video: json["url"]
                });
                tweet.appendChild(video2);
                //console.log("this should not happen!");
                break;
        }
        const qrtob = json["qrt"];

        if ((Object.keys(qrtob).length === 0 && Object.getPrototypeOf(qrtob) === Object.prototype) == false) {
            //console.log(json["qrt"]);
            const qrt = createEl("div", "quote");
            const qname = createEl("div", "qname", { inner: `QRT of : ${qrtob.handle} (@${qrtob.screenname})` });
            json["qrt"]["desc"] = json["qrt"]["desc"].replaceAll(/http.*t.co\S+/g, "");
            const qdesc = createEl("div", "qdesc", { inner: qrtob.desc });
            qrt.appendChild(qname);
            qrt.appendChild(qdesc);
            tweet.appendChild(qrt);
        }


        const meta = createEl("div", "meta");

        const rts = createEl("div", "cont", { inner: `${json["rts"]} Retweets` });
        const lks = createEl("div", "cont", { inner: `${json["likes"]} Likes` });

        const share = createEl("img", "share", { src: "/copy.svg" });

        meta.appendChild(rts);
        meta.appendChild(lks);
        meta.appendChild(share);
        tweet.appendChild(meta);
        bigArray.push(json["tweet"]);
        document.querySelector(".tweetCont").appendChild(tweet);
        document.querySelectorAll('img:not(.aimage,.share)').forEach(img => {
            imgPrev(img);
        });
        share.addEventListener("click", () =>
            navigator.clipboard.writeText(json["tweet"].replace("https://t", "https://fxt"))
        );
        tweetCount++;
    } else {
        if (bigArray.length > 100) //pro memory management 😎
            bigArray = [];
    }
}
