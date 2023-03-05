
using UdonSharp;
using UnityEngine;
using VRC.SDK3.Image;
using VRC.SDKBase;
using VRC.Udon;
using VRC.Udon.Common.Interfaces;

public class PhotoFrame : UdonSharpBehaviour
{
	public string Name;
	public VRCUrl Url;

	void Start()
	{
		var renderer = GetComponent<MeshRenderer>();
		if (!string.IsNullOrEmpty(Url.Get()) && renderer.material != null)
		{
			var downloader = new VRCImageDownloader();
			downloader.DownloadImage(Url, renderer.material, (IUdonEventReceiver)this);
		}
	}

	override public void OnImageLoadSuccess(IVRCImageDownload download)
	{
		Debug.Log(download.TextureInfo.FilterMode);
	}
}
